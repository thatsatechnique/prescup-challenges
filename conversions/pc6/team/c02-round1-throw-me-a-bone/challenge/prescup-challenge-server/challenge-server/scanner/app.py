from flask import Flask, request, render_template
from system_check import validate_and_check_host, check_system

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    ip = None
    if request.method == 'POST':
        ip = request.form['ip']

        host_check = validate_and_check_host(ip)
        if not host_check["valid_ip"]:
            result = {"error": "Invalid IP address or hostname"}
        elif not host_check["online"]:
            result = {"error": "Host is offline"}
        elif host_check["error"]:
            result = {"error": host_check["error"]}
        else:
            result = check_system(ip)

    return render_template('index.html', result=result, ip_address=ip)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=False)
