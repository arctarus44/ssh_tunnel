SPLIT_SIZE = 10


def RandomBody():
	yield RandomSection()
	if random.randrange(2) == 0:
		yield RandomBody()

def RandomSection():
	yield '<h1>'
	yield RandomSentence()
	yield '</h1>'
	sentences = random.randrange(5, 20)
	for _ in xrange(sentences):
		yield RandomSentence()

def RandomSentence():


def RandomWord():
	chars = random.randrange(2, 10)
	return ''.join(random.choice(string.ascii_lowercase) for _ in xrange(chars))

def Output(generator):
	if isinstance(generator, str):
		print generator
	else:
		for g in generator: Output(g)

Output(RandomHtml())

class HTMLGenerator:



	def __init__(self, marker, payload):



	def RandomHtml(self):
		yield '<html><body>'
		yield RandomBody()
		yield '</body></html>'
