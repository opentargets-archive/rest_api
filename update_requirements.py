__author__ = 'andreap'
import pip
with open("requirements.txt", "w") as f:
    for dist in pip.get_installed_distributions():
        req = dist.as_requirement()
        if 'flask-restful-swagger' in str(req):
            f.write("git+https://github.com/CTTV/flask-restful-swagger.git#egg=CTTV-swaggerui\n")
        else:
            f.write(str(req) + "\n")