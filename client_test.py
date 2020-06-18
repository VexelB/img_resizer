import requests
import unittest

class Tests(unittest.TestCase):
    def test_filepersist(self):
        response = requests.post('http://127.0.0.1:5000/', data = {'width' : '0', 'height' : '0'})
        self.assertEqual(response.text, 'No file part', msg = "Wrong file checking")
    def test_size(self):
        response = requests.post('http://127.0.0.1:5000/', data = {'width' : '0', 'height' : '0'}, files = {'file': ('ku.txt', 'ku')})
        self.assertEqual(response.text, 'Bad size', msg = "Wrong number in size checking")
    def test_filename(self):
        response = requests.post('http://127.0.0.1:5000/', data = {'width' : '1', 'height' : '1'}, files = {'file': ('ku.txt', 'ku')})
        self.assertEqual(response.text, 'No selected or wrong file', msg = "Wrong extension checking")
    def test_resultid(self):
        response = requests.post('http://127.0.0.1:5000/results', data = {'id' : -4})
        self.assertEqual(response.text, 'Wrong id!', msg = "Wrong id checking")
    def test_resultid(self):
        response = requests.post('http://127.0.0.1:5000/results', data = {'id' : 'mda'})
        self.assertEqual(response.text, 'Send integer please', msg = "Wrong converting to int")
    def test_result(self):
        with open('testpic.png', 'rb') as testpic:
            response = requests.post('http://127.0.0.1:5000/', data = {'width' : '10', 'height' : '10'}, files = {'file': testpic})
        id = int(response.text.split('<br>')[0].split('-')[1])
        response = requests.post('http://127.0.0.1:5000/results', data = {'id' : id})
        self.assertEqual(str(response), '<Response [200]>', msg = "Something wrong with pic getting")
if __name__ == '__main__':
    unittest.main()