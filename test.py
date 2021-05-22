import sys
import json
import requests


def main(argv):
    url = f"http://{argv[1]}:5010/score"

    if len(argv) > 2:
        data = open(argv[2], 'rb').read()
    else:
        data = open('images/dog.jpg', 'rb').read()

    res = requests.post(url, data=data)
    print(res.json())

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("usage : python3 test.py <IP Address> <path_to_image_file>")
    else:
        main(sys.argv)
