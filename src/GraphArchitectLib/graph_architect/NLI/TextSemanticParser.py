from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM


class NaturalToFormalTranslator:
    def __init__(self, model_name, device="cuda", max_length=512, top_k=50, top_p=0.9):
        """
        Инициализирует класс NaturalToFormalTranslator с указанной моделью и параметрами.

        Аргументы:
            model_name (str): Название или путь к предобученной модели
            device (str): Устройство для работы модели (по умолчанию: "cuda")
            max_length (int): Максимальная длина генерируемого текста (по умолчанию: 512)
            top_k (int): Количество топовых токенов для выборки (по умолчанию: 50)
            top_p (float): Кумулятивная вероятность для выборки по ядру (по умолчанию: 0.9)
        """
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.max_length = max_length
        self.top_k = top_k
        self.top_p = top_p

        self.qa_pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device_map=device,
            max_length=self.max_length,
            do_sample=True,
            top_k=self.top_k,
            top_p=self.top_p
        )

    def translate_task(self, task_text, max_gen_length=2500):
        """
        Переводит текст с естественного языка на формальный.

        Аргументы:
            task_text (str): Входной текст для перевода
            max_gen_length (int): Максимальная длина генерируемого текста (по умолчанию: 2500)

        Возвращает:
            str: Переведённый текст в формальном стиле
        """
        prompt = self.qa_pipeline.tokenizer.apply_chat_template(
            [{"role": "user", "content": task_text}],
            tokenize=False,
            add_generation_prompt=True
        )

        generated = self.qa_pipeline(
            prompt,
            max_length=max_gen_length,
            num_return_sequences=1
        )[0]["generated_text"]

        # Извлечение релевантной части ответа
        try:
            response = generated.split("Запрос:")[1].split("<|im_start|>assistant")[1]
        except IndexError:
            response = generated  # Возвращаем полный текст, если разделение не удалось

        return response

    def update_parameters(self, max_length=None, top_k=None, top_p=None):
        """
        Обновляет параметры генерации текста.

        Аргументы:
            max_length (int, опционально): Новая максимальная длина
            top_k (int, опционально): Новое значение top_k
            top_p (float, опционально): Новое значение top_p
        """
        if max_length is not None:
            self.max_length = max_length
        if top_k is not None:
            self.top_k = top_k
        if top_p is not None:
            self.top_p = top_p

        self.qa_pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device_map=self.qa_pipeline.device,
            max_length=self.max_length,
            do_sample=True,
            top_k=self.top_k,
            top_p=self.top_p
        )