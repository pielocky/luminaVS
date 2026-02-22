import cv2
import numpy as np
import easyocr
import os
import threading
from kivy.app import App
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.utils import platform
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.animation import Animation
from kivy.properties import NumericProperty, StringProperty, ListProperty, BooleanProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.text import LabelBase, DEFAULT_FONT
import tempfile
from gtts import gTTS
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple, Callable
import warnings
from pyzbar.pyzbar import decode as zbar_decode
from PIL import Image as PILImage
import sys

# Альтернатива pygame - используем playsound если доступно
try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False
    print("⚠️ playsound не установлен. Используйте: pip install playsound")

warnings.filterwarnings('ignore', category=UserWarning, module='easyocr')

# Настройки для мобильных устройств
if platform in ['android', 'ios']:
    Window.softinput_mode = 'below_target'

# Настройка шрифтов в зависимости от платформы
if platform == 'android':
    # На Android используем Roboto
    FONT_NAME = 'Roboto'
    FONT_LIGHT = 'Roboto'
    FONT_MEDIUM = 'Roboto'
elif platform == 'ios':
    # На iOS используем San Francisco или Helvetica
    FONT_NAME = 'Helvetica'
    FONT_LIGHT = 'Helvetica-Light'
    FONT_MEDIUM = 'Helvetica-Bold'
elif sys.platform == 'win32':
    # На Windows используем Segoe UI или Arial
    try:
        # Пробуем зарегистрировать Segoe UI
        LabelBase.register(name='SegoeUI', fn_regular='C:/Windows/Fonts/segoeui.ttf',
                          fn_bold='C:/Windows/Fonts/segoeuib.ttf')
        FONT_NAME = 'SegoeUI'
        FONT_LIGHT = 'SegoeUI'
        FONT_MEDIUM = 'SegoeUI'
    except:
        # Если не получилось, используем шрифт по умолчанию
        FONT_NAME = DEFAULT_FONT
        FONT_LIGHT = DEFAULT_FONT
        FONT_MEDIUM = DEFAULT_FONT
elif sys.platform == 'darwin':
    # На macOS используем системные шрифты
    FONT_NAME = '.AppleSystemUIFont'
    FONT_LIGHT = '.AppleSystemUIFont'
    FONT_MEDIUM = '.AppleSystemUIFont'
else:
    # На Linux используем шрифт по умолчанию
    FONT_NAME = DEFAULT_FONT
    FONT_LIGHT = DEFAULT_FONT
    FONT_MEDIUM = DEFAULT_FONT

# Современная цветовая схема - бело-голубая
COLORS = {
    'background': [0.98, 0.98, 1.0, 1],
    'surface': [1, 1, 1, 1],
    
    # Основные цвета
    'primary': [0.0, 0.6, 0.9, 1],
    'primary_light': [0.2, 0.7, 1.0, 1],
    'primary_dark': [0.0, 0.4, 0.7, 1],
    
    'success': [0.2, 0.8, 0.4, 1],
    'warning': [1.0, 0.6, 0.0, 1],
    'error': [1.0, 0.3, 0.3, 1],
    'purple': [0.6, 0.4, 0.9, 1],
    'gold': [1.0, 0.8, 0.2, 1],
    
    # Тень и границы
    'card_shadow': [0.0, 0.0, 0.0, 0.1],
    'card_border': [0.9, 0.95, 1.0, 1],
    
    # Текст
    'text_primary': [0.1, 0.2, 0.4, 1],
    'text_secondary': [0.4, 0.5, 0.7, 1],
    'text_on_primary': [1, 1, 1, 1],
    'text_dark': [0.1, 0.1, 0.2, 1],
}

@dataclass(frozen=True)
class AppConfig:
    """Конфигурация приложения"""
    CAMERA_ID: int = 0
    FPS: float = 1/30
    OCR_CONFIDENCE_THRESHOLD: float = 0.3
    TEMPLATES_DIR: str = "templates"
    SUPPORTED_EXTENSIONS: tuple = ('.jpg', '.jpeg', '.png', '.bmp')
    
    # Размеры
    BUTTON_HEIGHT: float = dp(52)
    BUTTON_HEIGHT_SMALL: float = dp(44)
    FONT_SIZE: float = sp(16)
    FONT_SIZE_SMALL: float = sp(14)
    FONT_SIZE_LARGE: float = sp(18)
    FONT_SIZE_HEADER: float = sp(22)
    PADDING: float = dp(12)
    PADDING_SMALL: float = dp(8)
    SPACING: float = dp(10)
    SPACING_SMALL: float = dp(5)
    BORDER_RADIUS: float = dp(12)
    CARD_ELEVATION: float = dp(2)

@dataclass
class ObjectTemplate:
    """Шаблон объекта"""
    name: str
    display_name: str
    threshold: float
    color: Tuple[int, int, int]

# Упрощенная стилизованная кнопка на основе стандартной Button
class StyledButton(Button):
    """Стилизованная кнопка с градиентным эффектом"""
    
    def __init__(self, color_type='primary', **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = AppConfig.BUTTON_HEIGHT
        self.font_size = AppConfig.FONT_SIZE
        self.bold = True
        self.font_name = FONT_MEDIUM
        
        # Убираем стандартный фон
        self.background_normal = ''
        self.background_down = ''
        self.background_color = [0, 0, 0, 0]
        
        # Цвет текста
        self.color = COLORS['text_on_primary']
        
        # Сохраняем тип цвета
        self.color_type = color_type
        
        # Обновляем градиент
        self.bind(pos=self._update_gradient, size=self._update_gradient)
    
    def _update_gradient(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Тень
            Color(*COLORS['card_shadow'])
            RoundedRectangle(pos=(self.x + AppConfig.CARD_ELEVATION, 
                                 self.y - AppConfig.CARD_ELEVATION),
                           size=self.size,
                           radius=[AppConfig.BORDER_RADIUS])
            
            # Основной фон в зависимости от типа
            if self.color_type == 'success':
                Color(*COLORS['success'])
            elif self.color_type == 'warning':
                Color(*COLORS['warning'])
            elif self.color_type == 'error':
                Color(*COLORS['error'])
            elif self.color_type == 'purple':
                Color(*COLORS['purple'])
            elif self.color_type == 'gold':
                Color(*COLORS['gold'])
            else:
                Color(*COLORS['primary'])
            
            RoundedRectangle(pos=self.pos, size=self.size,
                           radius=[AppConfig.BORDER_RADIUS])
            
            # Эффект при нажатии
            if self.state == 'down':
                Color(0, 0, 0, 0.1)
                RoundedRectangle(pos=self.pos, size=self.size,
                               radius=[AppConfig.BORDER_RADIUS])

class StyledToggleButton(ToggleButton):
    """Стилизованная переключаемая кнопка"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = AppConfig.BUTTON_HEIGHT
        self.font_size = AppConfig.FONT_SIZE
        self.bold = True
        self.font_name = FONT_MEDIUM
        
        # Убираем стандартный фон
        self.background_normal = ''
        self.background_down = ''
        self.background_color = [0, 0, 0, 0]
        
        # Цвет текста
        self.color = COLORS['text_on_primary']
        
        self.bind(pos=self._update_gradient, size=self._update_gradient, 
                  state=self._update_state)
    
    def _update_gradient(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Тень
            Color(*COLORS['card_shadow'])
            RoundedRectangle(pos=(self.x + AppConfig.CARD_ELEVATION, 
                                 self.y - AppConfig.CARD_ELEVATION),
                           size=self.size,
                           radius=[AppConfig.BORDER_RADIUS])
            
            # Основной фон
            if self.state == 'down':
                Color(*COLORS['primary_dark'])
            else:
                Color(*COLORS['primary'])
            
            RoundedRectangle(pos=self.pos, size=self.size,
                           radius=[AppConfig.BORDER_RADIUS])
    
    def _update_state(self, *args):
        self._update_gradient()

class ModernCard(BoxLayout):
    """Современная карточка с тенью"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = AppConfig.PADDING
        self.spacing = AppConfig.SPACING
        self.bind(pos=self._update_rect, size=self._update_rect)
        
    def _update_rect(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Тень
            Color(*COLORS['card_shadow'])
            RoundedRectangle(pos=(self.x + AppConfig.CARD_ELEVATION, 
                                 self.y - AppConfig.CARD_ELEVATION),
                           size=self.size,
                           radius=[AppConfig.BORDER_RADIUS])
            
            # Основной фон
            Color(*COLORS['surface'])
            RoundedRectangle(pos=self.pos, size=self.size,
                           radius=[AppConfig.BORDER_RADIUS])
            
            # Легкая обводка
            Color(*COLORS['card_border'])
            RoundedRectangle(pos=self.pos, size=self.size,
                           radius=[AppConfig.BORDER_RADIUS],
                           line_width=1)

class ModernLabel(Label):
    """Современный лейбл с красивым шрифтом"""
    
    def __init__(self, variant='primary', **kwargs):
        super().__init__(**kwargs)
        self.halign = 'left'
        self.valign = 'top'
        self.text_size = (None, None)
        
        # Настройки в зависимости от варианта
        if variant == 'primary':
            self.color = COLORS['text_primary']
            self.font_size = AppConfig.FONT_SIZE_LARGE
            self.bold = True
            self.font_name = FONT_MEDIUM
        elif variant == 'secondary':
            self.color = COLORS['text_secondary']
            self.font_size = AppConfig.FONT_SIZE_SMALL
            self.font_name = FONT_LIGHT
        elif variant == 'header':
            self.color = COLORS['primary']
            self.font_size = AppConfig.FONT_SIZE_HEADER
            self.bold = True
            self.font_name = FONT_MEDIUM
        elif variant == 'success':
            self.color = COLORS['success']
            self.font_size = AppConfig.FONT_SIZE
            self.font_name = FONT_MEDIUM
        elif variant == 'error':
            self.color = COLORS['error']
            self.font_size = AppConfig.FONT_SIZE
            self.font_name = FONT_MEDIUM
        else:
            self.font_name = FONT_NAME
        
        self.bind(size=self._update_text_size)
    
    def _update_text_size(self, *args):
        self.text_size = (self.width - AppConfig.PADDING * 2, None)

class TextToSpeech:
    """Синтезатор речи"""
    
    def __init__(self):
        self._lock = threading.Lock()
        
    def speak_text(self, text: str, lang: str = 'ru'):
        if not text:
            return
            
        with self._lock:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                    audio_file = f.name
                
                tts = gTTS(text=text, lang=lang, slow=False)
                tts.save(audio_file)
                
                if PLAYSOUND_AVAILABLE:
                    playsound(audio_file)
                else:
                    if sys.platform == 'win32':
                        os.system(f'start {audio_file}')
                    elif sys.platform == 'darwin':
                        os.system(f'afplay {audio_file}')
                    else:
                        os.system(f'ffplay -nodisp -autoexit {audio_file} 2>/dev/null')
                
                try:
                    os.unlink(audio_file)
                except:
                    pass
                    
            except Exception as e:
                print(f"Ошибка озвучивания: {e}")
    
    def stop_speaking(self):
        pass

class BarcodeReader:
    """Класс для распознавания штрих-кодов и QR-кодов"""
    
    def __init__(self, tts_callback: Optional[Callable] = None):
        self.tts_callback = tts_callback
    
    def decode_barcodes(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        """Распознает штрих-коды и QR-коды в кадре"""
        result = frame.copy()
        detections = []
        
        try:
            # Конвертируем OpenCV изображение в PIL
            pil_image = PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            # Декодируем все штрих-коды и QR-коды
            decoded_objects = zbar_decode(pil_image)
            
            for obj in decoded_objects:
                # Получаем данные
                barcode_data = obj.data.decode('utf-8')
                barcode_type = obj.type
                
                # Рисуем рамку вокруг кода
                points = obj.polygon
                if len(points) == 4:
                    pts = np.array([(p.x, p.y) for p in points], np.int32)
                    pts = pts.reshape((-1, 1, 2))
                    
                    # Цвет в зависимости от типа
                    color = COLORS['purple'][:3]  # RGB
                    color = tuple(int(c * 255) for c in color)
                    
                    cv2.polylines(result, [pts], True, color, 3)
                    
                    # Добавляем текст
                    display_text = f"{barcode_type}: {barcode_data[:20]}..."
                    if len(barcode_data) <= 20:
                        display_text = f"{barcode_type}: {barcode_data}"
                    
                    cv2.putText(result, display_text, 
                              (pts[0][0][0], pts[0][0][1] - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    
                    detections.append({
                        'type': barcode_type,
                        'data': barcode_data,
                        'bbox': obj.rect
                    })
        
        except Exception as e:
            print(f"Ошибка распознавания кода: {e}")
        
        return result, detections
    
    def speak_barcode(self, detections: List[Dict]):
        """Озвучивает распознанные коды"""
        if not detections or not self.tts_callback:
            return
        
        for detection in detections[:1]:  # Озвучиваем только первый код
            code_type = detection['type']
            code_data = detection['data']
            
            if code_type == 'QRCODE':
                text = f"QR код: {code_data}"
            else:
                text = f"Штрих код: {code_data}"
            
            threading.Thread(target=self.tts_callback, args=(text,), daemon=True).start()

class CurrencyRecognizer:
    """Класс для распознавания номинала купюр"""
    
    # База данных купюр (можно расширить)
    CURRENCY_DB = {
        'rub': {
            10: {'name': '10 рублей', 'color': 'зеленый', 'size': '150x65'},
            50: {'name': '50 рублей', 'color': 'синий', 'size': '150x65'},
            100: {'name': '100 рублей', 'color': 'коричневый', 'size': '150x65'},
            200: {'name': '200 рублей', 'color': 'зеленый', 'size': '150x65'},
            500: {'name': '500 рублей', 'color': 'фиолетовый', 'size': '150x65'},
            1000: {'name': '1000 рублей', 'color': 'бирюзовый', 'size': '157x69'},
            2000: {'name': '2000 рублей', 'color': 'синий', 'size': '157x69'},
            5000: {'name': '5000 рублей', 'color': 'красный', 'size': '157x69'}
        },
        'usd': {
            1: {'name': '1 доллар', 'color': 'зеленый', 'size': '156x66'},
            2: {'name': '2 доллара', 'color': 'зеленый', 'size': '156x66'},
            5: {'name': '5 долларов', 'color': 'фиолетовый', 'size': '156x66'},
            10: {'name': '10 долларов', 'color': 'желтый', 'size': '156x66'},
            20: {'name': '20 долларов', 'color': 'зеленый', 'size': '156x66'},
            50: {'name': '50 долларов', 'color': 'розовый', 'size': '156x66'},
            100: {'name': '100 долларов', 'color': 'зеленый', 'size': '156x66'}
        },
        'eur': {
            5: {'name': '5 евро', 'color': 'серый', 'size': '120x62'},
            10: {'name': '10 евро', 'color': 'красный', 'size': '127x67'},
            20: {'name': '20 евро', 'color': 'синий', 'size': '133x72'},
            50: {'name': '50 евро', 'color': 'оранжевый', 'size': '140x77'},
            100: {'name': '100 евро', 'color': 'зеленый', 'size': '147x82'},
            200: {'name': '200 евро', 'color': 'желтый', 'size': '153x82'},
            500: {'name': '500 евро', 'color': 'фиолетовый', 'size': '160x82'}
        }
    }
    
    def __init__(self, tts_callback: Optional[Callable] = None):
        self.tts_callback = tts_callback
        self.currency_type = 'rub'  # По умолчанию рубли
    
    def recognize_currency(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        """Распознает номинал купюры в кадре"""
        result = frame.copy()
        detections = []
        
        try:
            # Упрощенное распознавание на основе цветов и размеров
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                # Ищем прямоугольные области (потенциальные купюры)
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
                
                if len(approx) == 4:  # Прямоугольник
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Проверяем соотношение сторон (примерно как у купюры)
                    aspect_ratio = w / h if w > h else h / w
                    
                    if 1.5 < aspect_ratio < 3.0:  # Соотношение сторон купюры
                        # Анализируем цвет в области купюры
                        roi = frame[y:y+h, x:x+w]
                        avg_color = cv2.mean(roi)[:3]
                        
                        # Определяем номинал (упрощенно)
                        if self.currency_type == 'rub':
                            if avg_color[2] > 150:  # Красноватый
                                nominal = 5000
                            elif avg_color[0] > 150:  # Синеватый
                                nominal = 2000
                            elif avg_color[1] > 150:  # Зеленоватый
                                nominal = 100
                            else:
                                nominal = 500
                        else:
                            nominal = 100  # По умолчанию
                        
                        # Ищем в базе данных
                        currency_info = self.CURRENCY_DB.get(self.currency_type, {}).get(nominal)
                        
                        if currency_info:
                            display_name = currency_info['name']
                            color = COLORS['gold'][:3]
                            color = tuple(int(c * 255) for c in color)
                            
                            cv2.rectangle(result, (x, y), (x + w, y + h), color, 3)
                            cv2.putText(result, display_name, (x, y - 10),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                            
                            detections.append({
                                'currency': self.currency_type,
                                'nominal': nominal,
                                'display_name': display_name,
                                'bbox': (x, y, w, h)
                            })
        
        except Exception as e:
            print(f"Ошибка распознавания купюры: {e}")
        
        return result, detections
    
    def set_currency(self, currency_type: str):
        """Устанавливает тип валюты"""
        if currency_type in self.CURRENCY_DB:
            self.currency_type = currency_type
    
    def speak_currency(self, detection: Dict):
        """Озвучивает распознанную купюру"""
        if detection and self.tts_callback:
            text = f"Распознана купюра: {detection['display_name']}"
            threading.Thread(target=self.tts_callback, args=(text,), daemon=True).start()

class ObjectDetector:
    """Детектор объектов"""
    
    OBJECT_TEMPLATES = {
        'crosswalk': ObjectTemplate('crosswalk', '🚶 Переход', 0.65, (0, 150, 0)),
        'bus_stop': ObjectTemplate('bus_stop', '🚏 Остановка', 0.6, (150, 0, 0)),
        'medical_cross': ObjectTemplate('medical_cross', '🏥 Крест', 0.7, (0, 0, 150))
    }
    
    def __init__(self, tts_callback: Optional[Callable] = None):
        self.templates: Dict[str, np.ndarray] = {}
        self.last_detected: Dict[str, float] = {}
        self.tts_callback = tts_callback
        self.cooldown_time = 3
        
    def load_template(self, name: str, image_path: str) -> bool:
        if name not in self.OBJECT_TEMPLATES:
            return False
            
        try:
            template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if template is not None:
                self.templates[name] = template
                print(f"✓ Загружен: {self.OBJECT_TEMPLATES[name].display_name}")
                return True
        except:
            pass
        return False
    
    def load_default_templates(self) -> bool:
        if not os.path.exists(AppConfig.TEMPLATES_DIR):
            os.makedirs(AppConfig.TEMPLATES_DIR)
            return False
        
        loaded = 0
        for obj_name in self.OBJECT_TEMPLATES:
            for ext in AppConfig.SUPPORTED_EXTENSIONS:
                path = os.path.join(AppConfig.TEMPLATES_DIR, f"{obj_name}{ext}")
                if os.path.exists(path) and self.load_template(obj_name, path):
                    loaded += 1
                    break
        return loaded > 0
    
    def detect_objects(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        if not self.templates:
            return frame, []
        
        result = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detections = []
        new_detections = []
        
        for obj_name, template in self.templates.items():
            if gray.shape[0] < template.shape[0] or gray.shape[1] < template.shape[1]:
                continue
            
            match = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(match)
            obj_template = self.OBJECT_TEMPLATES.get(obj_name)
            
            if obj_template and max_val > obj_template.threshold:
                h, w = template.shape
                detection = {
                    'name': obj_name,
                    'display_name': obj_template.display_name,
                    'bbox': (max_loc, (max_loc[0] + w, max_loc[1] + h))
                }
                detections.append(detection)
                
                # Рисуем рамку
                cv2.rectangle(result, max_loc, (max_loc[0] + w, max_loc[1] + h), 
                            obj_template.color, 3)
                cv2.putText(result, obj_template.display_name, 
                          (max_loc[0], max_loc[1] - 10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, obj_template.color, 2)
                
                if self._should_speak(obj_name):
                    new_detections.append(detection)
                    self.last_detected[obj_name] = time.time()
        
        if new_detections and self.tts_callback:
            self._speak_detections(new_detections)
            
        return result, detections
    
    def _should_speak(self, obj_name: str) -> bool:
        if obj_name not in self.last_detected:
            return True
        return time.time() - self.last_detected[obj_name] > self.cooldown_time
    
    def _speak_detections(self, detections: List[Dict]):
        if detections:
            names = [d['display_name'].split(' ', 1)[1] for d in detections]
            text = f"Обнаружен {names[0]}" if len(names) == 1 else f"Обнаружены: {', '.join(names)}"
            threading.Thread(target=self.tts_callback, args=(text,), daemon=True).start()

class BarcodeTab(TabbedPanelItem):
    """Вкладка распознавания штрих-кодов и QR-кодов"""
    
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.text = '📱 Коды'
        self.is_active = False
        self.auto_speak = False
        self.last_detection = None
        
        layout = BoxLayout(orientation='vertical', padding=AppConfig.PADDING, spacing=AppConfig.SPACING)
        
        # Видео
        video_card = ModernCard(orientation='vertical', size_hint=(1, 0.4))
        self.image_widget = Image(size_hint=(1, 1))
        video_card.add_widget(self.image_widget)
        layout.add_widget(video_card)
        
        # Кнопки
        buttons_card = ModernCard(orientation='vertical', size_hint=(1, 0.3))
        btn_grid = BoxLayout(orientation='vertical', spacing=AppConfig.SPACING_SMALL)
        
        # Ряд 1
        row1 = BoxLayout(spacing=AppConfig.SPACING_SMALL, size_hint_y=None, height=AppConfig.BUTTON_HEIGHT)
        self.camera_btn = StyledToggleButton(text='▶ Камера')
        self.camera_btn.bind(on_press=self.toggle_camera)
        self.scan_btn = StyledButton(text='📷 Сканировать', color_type='purple')
        self.scan_btn.bind(on_press=self.scan_barcode)
        row1.add_widget(self.camera_btn)
        row1.add_widget(self.scan_btn)
        
        # Ряд 2
        row2 = BoxLayout(spacing=AppConfig.SPACING_SMALL, size_hint_y=None, height=AppConfig.BUTTON_HEIGHT)
        self.speak_btn = StyledButton(text='🔊 Озвучить', color_type='success')
        self.speak_btn.bind(on_press=self.speak_detection)
        self.stop_btn = StyledButton(text='⏹ Стоп', color_type='warning')
        self.stop_btn.bind(on_press=lambda x: self.app.tts.stop_speaking())
        row2.add_widget(self.speak_btn)
        row2.add_widget(self.stop_btn)
        
        # Ряд 3
        row3 = BoxLayout(spacing=AppConfig.SPACING_SMALL, size_hint_y=None, height=AppConfig.BUTTON_HEIGHT)
        self.auto_btn = StyledToggleButton(text='🎤 Авто')
        self.auto_btn.bind(on_press=self.toggle_auto)
        row3.add_widget(self.auto_btn)
        
        btn_grid.add_widget(row1)
        btn_grid.add_widget(row2)
        btn_grid.add_widget(row3)
        buttons_card.add_widget(btn_grid)
        layout.add_widget(buttons_card)
        
        # Результат
        result_card = ModernCard(orientation='vertical', size_hint=(1, 0.3))
        scroll = ScrollView()
        self.result_label = ModernLabel(
            variant='secondary',
            text='📱 Наведите камеру на QR-код или штрих-код',
            halign='center',
            valign='middle'
        )
        scroll.add_widget(self.result_label)
        result_card.add_widget(scroll)
        layout.add_widget(result_card)
        
        self.content = layout
    
    def toggle_camera(self, instance):
        if instance.state == 'down':
            self.start_camera()
            instance.text = '⏹ Стоп'
        else:
            self.stop_camera()
            instance.text = '▶ Камера'
    
    def toggle_auto(self, instance):
        self.auto_speak = instance.state == 'down'
        instance.text = '🎤 Авто ВКЛ' if self.auto_speak else '🎤 Авто'
    
    def start_camera(self):
        if not self.is_active:
            self.is_active = True
            Clock.schedule_interval(self.update_frame, AppConfig.FPS)
    
    def stop_camera(self):
        if self.is_active:
            Clock.unschedule(self.update_frame)
            self.is_active = False
            self.image_widget.texture = None
    
    def update_frame(self, dt):
        frame = self.app.get_current_frame()
        if frame is not None:
            if self.auto_speak:
                processed, detections = self.app.barcode_reader.decode_barcodes(frame)
                if detections:
                    self.last_detection = detections[0]
                    self._update_result(detections[0])
                    self.app.barcode_reader.speak_barcode(detections)
            else:
                processed, detections = self.app.barcode_reader.decode_barcodes(frame)
                if detections:
                    self.last_detection = detections[0]
                    self._update_result(detections[0])
            
            self.app.display_frame(processed, self.image_widget)
    
    def scan_barcode(self, instance):
        frame = self.app.get_current_frame()
        if frame is not None:
            self.result_label.text = "⏳ Сканирование..."
            self.result_label.color = COLORS['text_secondary']
            threading.Thread(target=self._scan, args=(frame.copy(),), daemon=True).start()
    
    def _scan(self, frame):
        try:
            processed, detections = self.app.barcode_reader.decode_barcodes(frame)
            if detections:
                self.last_detection = detections[0]
                Clock.schedule_once(lambda dt: self._update_result(detections[0]))
            else:
                Clock.schedule_once(lambda dt: self._update_no_result())
            Clock.schedule_once(lambda dt: self.app.display_frame(processed, self.image_widget))
        except:
            Clock.schedule_once(lambda dt: self._update_error())
    
    def _update_result(self, detection):
        self.result_label.text = f"{detection['type']}\n{detection['data']}"
        self.result_label.color = COLORS['purple']
    
    def _update_no_result(self):
        self.result_label.text = "❌ Код не найден"
        self.result_label.color = COLORS['error']
    
    def _update_error(self):
        self.result_label.text = "⚠️ Ошибка сканирования"
        self.result_label.color = COLORS['error']
    
    def speak_detection(self, instance):
        if self.last_detection:
            self.app.barcode_reader.speak_barcode([self.last_detection])

class CurrencyTab(TabbedPanelItem):
    """Вкладка распознавания купюр"""
    
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.text = '💰 Купюры'
        self.is_active = False
        self.auto_speak = False
        self.last_detection = None
        
        layout = BoxLayout(orientation='vertical', padding=AppConfig.PADDING, spacing=AppConfig.SPACING)
        
        # Видео
        video_card = ModernCard(orientation='vertical', size_hint=(1, 0.35))
        self.image_widget = Image(size_hint=(1, 1))
        video_card.add_widget(self.image_widget)
        layout.add_widget(video_card)
        
        # Кнопки
        buttons_card = ModernCard(orientation='vertical', size_hint=(1, 0.4))
        btn_grid = BoxLayout(orientation='vertical', spacing=AppConfig.SPACING_SMALL)
        
        # Ряд 1
        row1 = BoxLayout(spacing=AppConfig.SPACING_SMALL, size_hint_y=None, height=AppConfig.BUTTON_HEIGHT)
        self.camera_btn = StyledToggleButton(text='▶ Камера')
        self.camera_btn.bind(on_press=self.toggle_camera)
        self.recognize_btn = StyledButton(text='💰 Распознать', color_type='gold')
        self.recognize_btn.bind(on_press=self.recognize_currency)
        row1.add_widget(self.camera_btn)
        row1.add_widget(self.recognize_btn)
        
        # Ряд 2
        row2 = BoxLayout(spacing=AppConfig.SPACING_SMALL, size_hint_y=None, height=AppConfig.BUTTON_HEIGHT)
        self.speak_btn = StyledButton(text='🔊 Озвучить', color_type='success')
        self.speak_btn.bind(on_press=self.speak_detection)
        self.stop_btn = StyledButton(text='⏹ Стоп', color_type='warning')
        self.stop_btn.bind(on_press=lambda x: self.app.tts.stop_speaking())
        row2.add_widget(self.speak_btn)
        row2.add_widget(self.stop_btn)
        
        # Ряд 3
        row3 = BoxLayout(spacing=AppConfig.SPACING_SMALL, size_hint_y=None, height=AppConfig.BUTTON_HEIGHT)
        self.auto_btn = StyledToggleButton(text='🎤 Авто')
        self.auto_btn.bind(on_press=self.toggle_auto)
        row3.add_widget(self.auto_btn)
        
        # Ряд 4 - выбор валюты
        row4 = BoxLayout(spacing=AppConfig.SPACING_SMALL, size_hint_y=None, height=AppConfig.BUTTON_HEIGHT_SMALL)
        self.rub_btn = StyledToggleButton(text='🇷🇺 RUB')
        self.rub_btn.state = 'down'
        self.rub_btn.bind(on_press=lambda x: self.set_currency('rub'))
        self.usd_btn = StyledToggleButton(text='🇺🇸 USD')
        self.usd_btn.bind(on_press=lambda x: self.set_currency('usd'))
        self.eur_btn = StyledToggleButton(text='🇪🇺 EUR')
        self.eur_btn.bind(on_press=lambda x: self.set_currency('eur'))
        row4.add_widget(self.rub_btn)
        row4.add_widget(self.usd_btn)
        row4.add_widget(self.eur_btn)
        
        btn_grid.add_widget(row1)
        btn_grid.add_widget(row2)
        btn_grid.add_widget(row3)
        btn_grid.add_widget(row4)
        buttons_card.add_widget(btn_grid)
        layout.add_widget(buttons_card)
        
        # Результат
        result_card = ModernCard(orientation='vertical', size_hint=(1, 0.25))
        scroll = ScrollView()
        self.result_label = ModernLabel(
            variant='secondary',
            text='💰 Наведите камеру на купюру',
            halign='center',
            valign='middle'
        )
        scroll.add_widget(self.result_label)
        result_card.add_widget(scroll)
        layout.add_widget(result_card)
        
        self.content = layout
    
    def toggle_camera(self, instance):
        if instance.state == 'down':
            self.start_camera()
            instance.text = '⏹ Стоп'
        else:
            self.stop_camera()
            instance.text = '▶ Камера'
    
    def toggle_auto(self, instance):
        self.auto_speak = instance.state == 'down'
        instance.text = '🎤 Авто ВКЛ' if self.auto_speak else '🎤 Авто'
    
    def set_currency(self, currency_type):
        self.app.currency_recognizer.set_currency(currency_type)
        self.rub_btn.state = 'down' if currency_type == 'rub' else 'normal'
        self.usd_btn.state = 'down' if currency_type == 'usd' else 'normal'
        self.eur_btn.state = 'down' if currency_type == 'eur' else 'normal'
    
    def start_camera(self):
        if not self.is_active:
            self.is_active = True
            Clock.schedule_interval(self.update_frame, AppConfig.FPS)
    
    def stop_camera(self):
        if self.is_active:
            Clock.unschedule(self.update_frame)
            self.is_active = False
            self.image_widget.texture = None
    
    def update_frame(self, dt):
        frame = self.app.get_current_frame()
        if frame is not None:
            processed, detections = self.app.currency_recognizer.recognize_currency(frame)
            if detections:
                self.last_detection = detections[0]
                self._update_result(detections[0])
                if self.auto_speak:
                    self.app.currency_recognizer.speak_currency(detections[0])
            self.app.display_frame(processed, self.image_widget)
    
    def recognize_currency(self, instance):
        frame = self.app.get_current_frame()
        if frame is not None:
            self.result_label.text = "⏳ Распознавание..."
            self.result_label.color = COLORS['text_secondary']
            threading.Thread(target=self._recognize, args=(frame.copy(),), daemon=True).start()
    
    def _recognize(self, frame):
        try:
            processed, detections = self.app.currency_recognizer.recognize_currency(frame)
            if detections:
                self.last_detection = detections[0]
                Clock.schedule_once(lambda dt: self._update_result(detections[0]))
            else:
                Clock.schedule_once(lambda dt: self._update_no_result())
            Clock.schedule_once(lambda dt: self.app.display_frame(processed, self.image_widget))
        except:
            Clock.schedule_once(lambda dt: self._update_error())
    
    def _update_result(self, detection):
        self.result_label.text = f"💰 {detection['display_name']}"
        self.result_label.color = COLORS['gold']
    
    def _update_no_result(self):
        self.result_label.text = "❌ Купюра не найдена"
        self.result_label.color = COLORS['error']
    
    def _update_error(self):
        self.result_label.text = "⚠️ Ошибка распознавания"
        self.result_label.color = COLORS['error']
    
    def speak_detection(self, instance):
        if self.last_detection:
            self.app.currency_recognizer.speak_currency(self.last_detection)

class ObjectDetectionTab(TabbedPanelItem):
    """Вкладка детектирования объектов"""
    
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.text = '🎯 Детектор'
        self.is_active = False
        
        layout = BoxLayout(orientation='vertical', padding=AppConfig.PADDING, spacing=AppConfig.SPACING)
        
        # Информация
        info_card = ModernCard(orientation='vertical', size_hint_y=None, height=dp(80))
        self.info_label = ModernLabel(variant='secondary', text='📁 Загрузите шаблоны', 
                                     halign='center', valign='middle', size_hint_y=None, height=dp(40))
        self.status_label = ModernLabel(variant='success', text='✅ Готов', 
                                       halign='center', valign='middle', size_hint_y=None, height=dp(40))
        info_card.add_widget(self.info_label)
        info_card.add_widget(self.status_label)
        layout.add_widget(info_card)
        
        # Видео
        video_card = ModernCard(orientation='vertical', size_hint=(1, 0.45))
        self.image_widget = Image(size_hint=(1, 1))
        video_card.add_widget(self.image_widget)
        layout.add_widget(video_card)
        
        # Кнопки
        buttons_card = ModernCard(orientation='vertical', size_hint_y=None, height=dp(130))
        btn_grid = BoxLayout(orientation='vertical', spacing=AppConfig.SPACING_SMALL)
        
        row1 = BoxLayout(spacing=AppConfig.SPACING_SMALL, size_hint_y=None, height=AppConfig.BUTTON_HEIGHT)
        self.btn_load = StyledButton(text='📁 Шаблоны')
        self.btn_load.bind(on_press=self.app.show_template_loader)
        self.btn_camera = StyledToggleButton(text='▶ Камера')
        self.btn_camera.bind(on_press=self.toggle_camera)
        row1.add_widget(self.btn_load)
        row1.add_widget(self.btn_camera)
        
        row2 = BoxLayout(spacing=AppConfig.SPACING_SMALL, size_hint_y=None, height=AppConfig.BUTTON_HEIGHT)
        self.btn_speak = StyledButton(text='🔊 Озвучить', color_type='success')
        self.btn_speak.bind(on_press=self.speak_detections)
        row2.add_widget(self.btn_speak)
        
        btn_grid.add_widget(row1)
        btn_grid.add_widget(row2)
        buttons_card.add_widget(btn_grid)
        layout.add_widget(buttons_card)
        
        self.content = layout
    
    def toggle_camera(self, instance):
        if instance.state == 'down':
            self.start_camera()
            instance.text = '⏹ Стоп'
        else:
            self.stop_camera()
            instance.text = '▶ Камера'
    
    def start_camera(self):
        if not self.is_active:
            self.is_active = True
            Clock.schedule_interval(self.update_frame, AppConfig.FPS)
    
    def stop_camera(self):
        if self.is_active:
            Clock.unschedule(self.update_frame)
            self.is_active = False
            self.image_widget.texture = None
    
    def update_frame(self, dt):
        frame = self.app.get_current_frame()
        if frame is not None:
            processed, detections = self.app.detector.detect_objects(frame)
            self.app.last_detections = detections
            
            if detections:
                names = [d['display_name'] for d in detections[:2]]
                text = "🔍 " + ", ".join(names)
                if len(detections) > 2:
                    text += f" +{len(detections)-2}"
                self.status_label.text = text
                self.status_label.color = COLORS['success']
            else:
                self.status_label.text = "🔍 Поиск..."
                self.status_label.color = COLORS['text_secondary']
            
            self.app.display_frame(processed, self.image_widget)
    
    def speak_detections(self, instance):
        if hasattr(self.app, 'last_detections') and self.app.last_detections:
            self.app.detector._speak_detections(self.app.last_detections)

class OCRTab(TabbedPanelItem):
    """Вкладка распознавания текста"""
    
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.text = '📝 OCR'
        self.is_active = False
        self.last_text = ""
        self.auto_speak = False
        
        layout = BoxLayout(orientation='vertical', padding=AppConfig.PADDING, spacing=AppConfig.SPACING)
        
        # Видео
        video_card = ModernCard(orientation='vertical', size_hint=(1, 0.4))
        self.image_widget = Image(size_hint=(1, 1))
        video_card.add_widget(self.image_widget)
        layout.add_widget(video_card)
        
        # Кнопки
        buttons_card = ModernCard(orientation='vertical', size_hint=(1, 0.3))
        btn_grid = BoxLayout(orientation='vertical', spacing=AppConfig.SPACING_SMALL)
        
        row1 = BoxLayout(spacing=AppConfig.SPACING_SMALL, size_hint_y=None, height=AppConfig.BUTTON_HEIGHT)
        self.camera_btn = StyledToggleButton(text='▶ Камера')
        self.camera_btn.bind(on_press=self.toggle_camera)
        self.recognize_btn = StyledButton(text='📷 Распознать')
        self.recognize_btn.bind(on_press=self.capture_and_recognize)
        row1.add_widget(self.camera_btn)
        row1.add_widget(self.recognize_btn)
        
        row2 = BoxLayout(spacing=AppConfig.SPACING_SMALL, size_hint_y=None, height=AppConfig.BUTTON_HEIGHT)
        self.speak_btn = StyledButton(text='🔊 Озвучить', color_type='success')
        self.speak_btn.bind(on_press=self.speak_text)
        self.stop_btn = StyledButton(text='⏹ Стоп', color_type='warning')
        self.stop_btn.bind(on_press=lambda x: self.app.tts.stop_speaking())
        row2.add_widget(self.speak_btn)
        row2.add_widget(self.stop_btn)
        
        row3 = BoxLayout(spacing=AppConfig.SPACING_SMALL, size_hint_y=None, height=AppConfig.BUTTON_HEIGHT)
        self.auto_btn = StyledToggleButton(text='🎤 Авто')
        self.auto_btn.bind(on_press=self.toggle_auto)
        row3.add_widget(self.auto_btn)
        
        btn_grid.add_widget(row1)
        btn_grid.add_widget(row2)
        btn_grid.add_widget(row3)
        buttons_card.add_widget(btn_grid)
        layout.add_widget(buttons_card)
        
        # Результат
        result_card = ModernCard(orientation='vertical', size_hint=(1, 0.3))
        scroll = ScrollView()
        self.result_label = ModernLabel(
            variant='secondary',
            text='📄 Текст будет здесь',
            halign='center',
            valign='middle'
        )
        scroll.add_widget(self.result_label)
        result_card.add_widget(scroll)
        layout.add_widget(result_card)
        
        self.content = layout
    
    def toggle_camera(self, instance):
        if instance.state == 'down':
            self.start_camera()
            instance.text = '⏹ Стоп'
        else:
            self.stop_camera()
            instance.text = '▶ Камера'
    
    def toggle_auto(self, instance):
        self.auto_speak = instance.state == 'down'
        instance.text = '🎤 Авто ВКЛ' if self.auto_speak else '🎤 Авто'
    
    def start_camera(self):
        if not self.is_active:
            self.is_active = True
            Clock.schedule_interval(self.update_frame, AppConfig.FPS)
    
    def stop_camera(self):
        if self.is_active:
            Clock.unschedule(self.update_frame)
            self.is_active = False
            self.image_widget.texture = None
    
    def update_frame(self, dt):
        frame = self.app.get_current_frame()
        if frame is not None:
            self.app.display_frame(frame, self.image_widget)
    
    def capture_and_recognize(self, instance):
        frame = self.app.get_current_frame()
        if frame is not None:
            self.result_label.text = "⏳ Распознавание..."
            self.result_label.color = COLORS['text_secondary']
            threading.Thread(target=self._recognize, args=(frame.copy(),), daemon=True).start()
    
    def _recognize(self, frame):
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            
            results = self.app.reader.readtext(gray, paragraph=True)
            texts = [text for (_, text, prob) in results if prob > AppConfig.OCR_CONFIDENCE_THRESHOLD]
            
            if texts:
                result = "📝 " + " ".join(texts)
                color = COLORS['success']
                if self.auto_speak:
                    threading.Thread(
                        target=self.app.tts.speak_text,
                        args=(f"Распознано: {result[2:]}",),
                        daemon=True
                    ).start()
            else:
                result = "❌ Текст не найден"
                color = COLORS['error']
            
            Clock.schedule_once(lambda dt: self._update_result(result, color))
        except:
            Clock.schedule_once(lambda dt: self._update_result("⚠️ Ошибка", COLORS['error']))
    
    def _update_result(self, text, color):
        self.result_label.text = text
        self.result_label.color = color
        self.last_text = text
    
    def speak_text(self, instance):
        if self.last_text and "❌" not in self.last_text and "⚠️" not in self.last_text:
            clean = self.last_text.replace("📝 ", "")
            threading.Thread(target=self.app.tts.speak_text, args=(clean,), daemon=True).start()

class TemplateLoaderPopup(Popup):
    """Попап загрузки шаблонов"""
    
    def __init__(self, detector, callback, **kwargs):
        super().__init__(**kwargs)
        self.detector = detector
        self.callback = callback
        self.title = "📁 Загрузка шаблона"
        self.size_hint = (0.95, 0.9)
        
        layout = BoxLayout(orientation='vertical', padding=AppConfig.PADDING, spacing=AppConfig.SPACING)
        
        # Заголовок
        title_label = ModernLabel(variant='header', text="Выберите тип объекта:", 
                                 halign='center', size_hint_y=None, height=dp(50))
        layout.add_widget(title_label)
        
        # Выбранный тип
        self.type_label = ModernLabel(variant='secondary', text="❌ Не выбран", 
                                     halign='center', size_hint_y=None, height=dp(40))
        layout.add_widget(self.type_label)
        
        # Кнопки выбора
        for obj_id, obj_template in ObjectDetector.OBJECT_TEMPLATES.items():
            btn = StyledButton(text=obj_template.display_name)
            btn.size_hint_y = None
            btn.height = dp(48)
            btn.obj_id = obj_id
            btn.bind(on_press=self.select_type)
            layout.add_widget(btn)
        
        # Файловый выбор
        self.filechooser = FileChooserListView(
            filters=[f'*{ext}' for ext in AppConfig.SUPPORTED_EXTENSIONS],
            size_hint=(1, 0.4)
        )
        layout.add_widget(self.filechooser)
        
        # Кнопки действий
        btn_layout = BoxLayout(size_hint_y=None, height=AppConfig.BUTTON_HEIGHT, spacing=AppConfig.SPACING)
        load_btn = StyledButton(text='✅ Загрузить', color_type='success')
        load_btn.bind(on_press=self.load_template)
        cancel_btn = StyledButton(text='❌ Отмена', color_type='warning')
        cancel_btn.bind(on_press=self.dismiss)
        btn_layout.add_widget(load_btn)
        btn_layout.add_widget(cancel_btn)
        layout.add_widget(btn_layout)
        
        self.selected_object = None
        self.content = layout
    
    def select_type(self, instance):
        self.selected_object = instance.obj_id
        self.type_label.text = f"✅ {instance.text}"
        self.type_label.color = COLORS['success']
    
    def load_template(self, instance):
        if self.selected_object and self.filechooser.selection:
            path = self.filechooser.selection[0]
            if self.detector.load_template(self.selected_object, path):
                self.callback()
                self.dismiss()

class CameraApp(TabbedPanel):
    """Основное приложение"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_default_tab = False
        self.tab_width = Window.width / 4
        self.tab_height = dp(60)
        
        # Компоненты
        self.tts = TextToSpeech()
        self.detector = ObjectDetector(tts_callback=self.tts.speak_text)
        self.barcode_reader = BarcodeReader(tts_callback=self.tts.speak_text)
        self.currency_recognizer = CurrencyRecognizer(tts_callback=self.tts.speak_text)
        self.reader = easyocr.Reader(['ru', 'en'], gpu=False)
        
        # Переменные
        self.capture = None
        self.test_mode = False
        self.last_detections = []
        
        # Вкладки
        self.detection_tab = ObjectDetectionTab(self)
        self.ocr_tab = OCRTab(self)
        self.barcode_tab = BarcodeTab(self)
        self.currency_tab = CurrencyTab(self)
        
        self.add_widget(self.detection_tab)
        self.add_widget(self.ocr_tab)
        self.add_widget(self.barcode_tab)
        self.add_widget(self.currency_tab)
        
        # Инициализация
        self._init_camera()
        self._init_templates()
    
    def _init_camera(self):
        try:
            self.capture = cv2.VideoCapture(AppConfig.CAMERA_ID)
            if platform in ['android', 'ios']:
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            if not self.capture.isOpened():
                raise Exception()
            self.test_mode = False
        except:
            self.test_mode = True
    
    def _init_templates(self):
        if self.detector.load_default_templates():
            self.detection_tab.info_label.text = "✅ Шаблоны загружены"
            self.detection_tab.info_label.color = COLORS['success']
        else:
            self.detection_tab.info_label.text = "📁 Загрузите шаблоны"
            self.detection_tab.info_label.color = COLORS['warning']
    
    def get_current_frame(self):
        if self.test_mode:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "📷 КАМЕРА НЕ НАЙДЕНА", (120, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            return frame
        
        if self.capture and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                return frame
        return None
    
    @staticmethod
    def display_frame(frame, widget):
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            max_w = int(Window.width * 0.9)
            if w > max_w:
                scale = max_w / w
                rgb = cv2.resize(rgb, (max_w, int(h * scale)))
            
            texture = Texture.create(size=(rgb.shape[1], rgb.shape[0]), colorfmt='rgb')
            texture.blit_buffer(cv2.flip(rgb, 0).tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            widget.texture = texture
        except:
            pass
    
    def show_template_loader(self, instance):
        TemplateLoaderPopup(self.detector, self._on_templates_loaded).open()
    
    def _on_templates_loaded(self):
        count = len(self.detector.templates)
        self.detection_tab.info_label.text = f"✅ Загружено: {count}"
        self.detection_tab.info_label.color = COLORS['success']
    
    def on_stop(self):
        self.detection_tab.stop_camera()
        self.ocr_tab.stop_camera()
        self.barcode_tab.stop_camera()
        self.currency_tab.stop_camera()
        if self.capture:
            self.capture.release()

class MainApp(App):
    """Главное приложение"""
    
    def build(self):
        self.title = "🎯 Vision Assist"
        if platform not in ['android', 'ios']:
            Window.size = (dp(400), dp(750))
        return CameraApp()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🎯 VISION ASSIST")
    print("="*50)
    print("\n✨ Современный интерфейс с системными шрифтами")
    print("🎯 Детектирование объектов")
    print("📝 Распознавание текста (OCR)")
    print("📱 Распознавание QR и штрих-кодов")
    print("💰 Распознавание номинала купюр")
    print("🔊 Озвучивание всех результатов")
    print("\n📁 Папка 'templates' для шаблонов")
    print("="*50 + "\n")
    
    if not PLAYSOUND_AVAILABLE:
        print("⚠️ Для лучшего воспроизведения звука установите playsound:")
        print("   pip install playsound")
        print()
    
    try:
        MainApp().run()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        if platform not in ['android', 'ios']:
            input("\nНажмите Enter...")