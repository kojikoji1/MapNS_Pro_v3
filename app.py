from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import os, csv
from PIL import Image
import exifread

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
DATA_FILE = 'data/projects.csv'

def get_gps_and_date(file_path):
    with open(file_path, 'rb') as f:
        tags = exifread.process_file(f)
    try:
        lat = tags['GPS GPSLatitude']
        lon = tags['GPS GPSLongitude']
        lat_ref = tags['GPS GPSLatitudeRef'].values
        lon_ref = tags['GPS GPSLongitudeRef'].values
        date = tags.get('EXIF DateTimeOriginal', None)
        def conv(val):
            d, m, s = [float(x.num) / float(x.den) for x in val.values]
            return d + m / 60 + s / 3600
        latitude = conv(lat)
        longitude = conv(lon)
        if lat_ref != 'N':
            latitude = -latitude
        if lon_ref != 'E':
            longitude = -longitude
        return latitude, longitude, str(date)
    except:
        return None, None, None

@app.route('/', methods=['GET', 'POST'])
def project_select():
    if request.method == 'POST':
        project_name = request.form['project_name']
        return redirect(url_for('map_view', project=project_name))
    projects = set()
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 1:
                    projects.add(row[0])
    return render_template('project_select.html', projects=sorted(projects))

@app.route('/project/<project>', methods=['GET', 'POST'])
def map_view(project):
    message = None
    if request.method == 'POST':
        file = request.files['photo']
        comment = request.form['comment']
        if file:
            filename = file.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            lat, lon, date = get_gps_and_date(save_path)
            if lat and lon:
                with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([project, filename, comment, lat, lon, date])
                return redirect(url_for('map_view', project=project))
            else:
                message = "※ 位置情報がありませんでした。"

    markers = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 6 and row[0] == project and row[3] and row[4]:
                    markers.append({
                        'filename': row[1],
                        'comment': row[2],
                        'lat': float(row[3]),
                        'lon': float(row[4]),
                        'date': row[5]
                    })
    return render_template('map_view.html', project=project, markers=markers, message=message)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
