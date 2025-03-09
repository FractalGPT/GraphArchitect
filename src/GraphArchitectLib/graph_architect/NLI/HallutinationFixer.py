from scipy.spatial import distance

# ToDo: Добавить векторизацию всех элементов выхода llm и fix для всей структуры
class HFixerWithDictionary:
    """Класс для автоматического исправления галлюцинаций при заполнении форм с
     известными ответами, например, когда LLM пишет синоним"""

    def __init__(self, metric='cosine'):
        """
        :param metric: Метрика расстояния (по умолчанию 'cosine'). Возможные значения:
            - 'cosine' (косинусное расстояние)
            - 'euclidean' (евклидово расстояние)
            - 'cityblock' (манхэттенское расстояние)
            - 'chebyshev' (расстояние Чебышева)
            - 'minkowski' (расстояние Минковского)
        :raises ValueError: если передана недопустимая метрика.
        """
        valid_metrics = {'cosine', 'euclidean', 'cityblock', 'chebyshev', 'minkowski'}
        if metric not in valid_metrics:
            raise ValueError(f"Недопустимая метрика: {metric}. Доступные метрики: {valid_metrics}")

        self.metric = metric

    def fix(self, element_vector, knn_candidates):
        """
        Выбирает ближайший элемент к векторизованному и возвращает его.

        :param element_vector: Вектор элемента, который нужно исправить.
        :param knn_candidates: Список кортежей (ключ, вектор) возможных кандидатов.
        :return: Ключ ближайшего кандидата.
        """
        if not knn_candidates:
            raise ValueError("Список кандидатов пуст.")

        closest_candidate = min(knn_candidates,
                                key=lambda x: distance.cdist([element_vector],
                                                             [x[1]], metric=self.metric)[0][0])
        return closest_candidate[0]
