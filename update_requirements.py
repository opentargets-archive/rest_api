__author__ = 'andreap'
import pip
with open("requirements.txt", "w") as f:
    for dist in pip.get_installed_distributions():
        req = dist.as_requirement()
        if 'flask-restful-swagger' in str(req):
            f.write("-e git+https://github.com/CTTV/flask-restful-swagger.git@657faa7377f5dcf7718f4e094d50aa2dd86999cf#egg=flask_restful_swagger-master\n")
        else:
            f.write(str(req) + "\n")