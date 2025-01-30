class TextUtils:
    @staticmethod
    def read_context(filename: str) -> str:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
