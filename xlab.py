import xml.etree.ElementTree as XmlElementTree
import httplib2
import uuid
from config import ***

***_HOST = '***'
***_PATH = '/***_xml'
CHUNK_SIZE = 1024 ** 2

def speech_to_text(filename=None, bytes=None, request_id=uuid.uuid4().hex, topic='notes', lang='ru-RU',
               	key=***_API_KEY):
    # если есть бинарный файл то читаем его
	if filename:
    	with open(filename, 'br') as file:
        	bytes = file.read()
	if not bytes:
    	raise Exception('Neither file name nor bytes provided.')

    # конвертируем бинарный файловый объект в PCM 16000 Гц 16 бит
	bytes = convert_to_pcm16b16000r(in_bytes=bytes)

    # собираем урлу для API запроса
	url = ***_PATH + '?uuid=%s&key=%s&topic=%s&lang=%s' % (
    	request_id,
    	key,
    	topic,
    	lang
	)

    # разбиваем байты на блоки
	chunks = read_chunks(CHUNK_SIZE, bytes)

    # установка соединения
	connection = httplib2.HTTPConnectionWithTimeout(***_HOST)
    # настраиваем запрос (метод, хэдеры)
	connection.connect()
	connection.putrequest('POST', url)
	connection.putheader('Transfer-Encoding', 'chunked')
	connection.putheader('Content-Type', 'audio/x-pcm;bit=16;rate=16000')
	connection.endheaders()

    # отправляем блоки
	for chunk in chunks:
    	connection.send(('%s\r\n' % hex(len(chunk))[2:]).encode())
    	connection.send(chunk)
    	connection.send('\r\n'.encode())

	connection.send('0\r\n\r\n'.encode())
	response = connection.getresponse()

    # принимаем ответ и обрабатываем. Если 200 читаем xml и создаем xml tree
	if response.code == 200:
    	response_text = response.read()
    	xml = XmlElementTree.fromstring(response_text)

    	if int(xml.attrib['success']) == 1:
        	max_confidence = - float("inf")
        	text = ''
            # ищем распознование голоса с максимальной уверенностью (confidence)
        	for child in xml:
            	if float(child.attrib['confidence']) > max_confidence:
                	text = child.text
                	max_confidence = float(child.attrib['confidence'])
            # если confidence не минус бесконечность как вначале возвращаем результат распознавания
	        if max_confidence != - float("inf"):
            	return text
        	else:
                # рейзим исключения
            	raise SpeechException('No text found.\n\nResponse:\n%s' % (response_text))
    	else:
        	raise SpeechException('No text found.\n\nResponse:\n%s' % (response_text))
	else:
    	raise SpeechException('Unknown error.\nCode: %s\n\n%s' % (response.code, response.read()))

сlass SpeechException(Exception):
	pass
