class File:

    def __init__(self, file_path):
        self.text = open(file_path).read()
        self.lines = self.text.split('\n')
        self.deprecated_count = 0
        self.removed_count = 0
