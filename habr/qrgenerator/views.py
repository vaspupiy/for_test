from django.shortcuts import render
from qrcode import make as make_qr


def index(request):
    qr_image = False

    if request.method == "POST":
        data = request.POST['data']
        domen_name = request.get_host()
        path_name = request.path
        ful_path_name = request.get_full_path()
        img = make_qr(data)
        img.save("media/qr/test.png")
        qr_image = True
        print(domen_name, path_name, ful_path_name)

    response = {
        'qr_image': qr_image
    }

    return render(request, 'qrgenerator/index.html', response)
