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
from kivy.graphics import Color, RoundedRectangle
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
import gc
from functools import lru_cache, partial

# Оптимизация для Android
if platform == 'android':
    import android
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE, 
                        Permission.READ_EXTERNAL_STORAGE])

# Упрощенное воспроизведение звука для Android
try:
    from android.media import MediaPlayer
    ANDROID_MEDIA = True
except:
    ANDROID_MEDIA = False

try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False

warnings.filterwarnings('ignore')

# Настройки для Android
if platform == 'android':
    Window.softinput_mode = 'below_target'
    # Ограничиваем разрешение для производительности
    MAX_FRAME_WIDTH = 480
    MAX_FRAME_HEIGHT = 360
else:
    MAX_FRAME_WIDTH = 640
    MAX_FRAME_HEIGHT = 480

# Настройка шрифтов
if platform == 'android':
    FONT_NAME = 'Roboto'
    FONT_LIGHT = 'Roboto'
    FONT_MEDIUM = 'Roboto'
else:
    FONT_NAME = DEFAULT_FONT
    FONT_LIGHT = DEFAULT_FONT
    FONT_MEDIUM = DEFAULT_FONT

# Оптимизированная цветовая схема
COLORS = {
    'background': [0.98, 0.98, 1.0, 1],
    'surface': [1, 1, 1, 1],
    'primary': [0.0, 0.6, 0.9, 1],
    'primary_dark': [0.0, 0.4, 0.7, 1],
    'success': [0.2, 0.8, 0.4, 1],
    'warning': [1.0, 0.6, 0.0, 1],
    'error': [1.0, 0.3, 0.3, 1],
    'purple': [0.6, 0.4, 0.9, 1],
    'gold': [1.0, 0.8, 0.2, 1],
    'card_shadow': [0.0, 0.0, 0.0, 0.1],
    'card_border': [0.9, 0.95, 1.0, 1],
    'text_primary': [0.1, 0.2, 0.4, 1],
    'text_secondary': [0.4, 0.5, 0.7, 1],
    'text_on_primary': [1, 1, 1, 1],
}

@dataclass(frozen=True)
class AppConfig:
    CAMERA_ID: int = 0
    FPS: float = 1/15  # Уменьшено для производительности
    OCR_CONFIDENCE_THRESHOLD: float = 0.3
    TEMPLATES_DIR: str = "templates"
    SUPPORTED_EXTENSIONS: tuple = ('.jpg', '.jpeg', '.png', '.bmp')
    
    # Оптимизированные размеры для Android
    BUTTON_HEIGHT: float = dp(48)
    BUTTON_HEIGHT_SMALL: float = dp(40)
    FONT_SIZE: float = sp(14)
    FONT_SIZE_SMALL: float = sp(12)
    FONT_SIZE_LARGE: float = sp(16)
    FONT_SIZE_HEADER: float = sp(18)
    PADDING: float = dp(8)
    SPACING: float = dp(5)
    BORDER_RADIUS: float = dp(8)
    CARD_ELEVATION: float = dp(1)

@dataclass
class ObjectTemplate:
    name: str
    display_name: str
    threshold: float
    color: Tuple[int, int, int]

# Оптимизированная кнопка с кэшированием
class StyledButton(Button):
    def __init__(self, color_type='primary', **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = AppConfig.BUTTON_HEIGHT
        self.font_size = AppConfig.FONT_SIZE
        self.bold = True
        self.font_name = FONT_MEDIUM
        self.background_normal = ''
        self.background_down = ''
        self.background_color = [0, 0, 0, 0]
        self.color = COLORS['text_on_primary']
        self.color_type = color_type
        self._cached_bg = None
        self.bind(pos=self._update_gradient, size=self._update_gradient)
    
    def _update_gradient(self, *args):
        if self._cached_bg == (self.x, self.y, self.width, self.height, self.state):
            return
        self._cached_bg = (self.x, self.y, self.width, self.height, self.state)
        
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS['card_shadow'])
            RoundedRectangle(pos=(self.x + AppConfig.CARD_ELEVATION, 
                                 self.y - AppConfig.CARD_ELEVATION),
                           size=self.size,
                           radius=[AppConfig.BORDER_RADIUS])
            
            color_map = {
                'success': COLORS['success'],
                'warning': COLORS['warning'],
                'error': COLORS['error'],
                'purple': COLORS['purple'],
                'gold': COLORS['gold']
            }
            Color(*color_map.get(self.color_type, COLORS['primary']))
            
            RoundedRectangle(pos=self.pos, size=self.size,
                           radius=[AppConfig.BORDER_RADIUS])
            
            if self.state == 'down':
                Color(0, 0, 0, 0.1)
                RoundedRectangle(pos=self.pos, size=self.size,
                               radius=[AppConfig.BORDER_RADIUS])

class StyledToggleButton(ToggleButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = AppConfig.BUTTON_HEIGHT
        self.font_size = AppConfig.FONT_SIZE
        self.bold = True
        self.font_name = FONT_MEDIUM
        self.background_normal = ''
        self.background_down = ''
        self.background_color = [0, 0, 0, 0]
        self.color = COLORS['text_on_primary']
        self._cached_bg = None
        self.bind(pos=self._update_gradient, size=self._update_gradient, 
                  state=self._update_state)
    
    def _update_gradient(self, *args):
        if self._cached_bg == (self.x, self.y, self.width, self.height, self.state):
            return
        self._cached_bg = (self.x, self.y, self.width, self.height, self.state)
        
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS['card_shadow'])
            RoundedRectangle(pos=(self.x + AppConfig.CARD_ELEVATION, 
                                 self.y - AppConfig.CARD_ELEVATION),
                           size=self.size,
                           radius=[AppConfig.BORDER_RADIUS])
            
            Color(*COLORS['primary_dark'] if self.state == 'down' else COLORS['primary'])
            RoundedRectangle(pos=self.pos, size=self.size,
                           radius=[AppConfig.BORDER_RADIUS])
    
    def _update_state(self, *args):
        self._update_gradient()

class ModernCard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = AppConfig.PADDING
        self.spacing = AppConfig.SPACING
        self._cached_rect = None
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _update_rect(self, *args):
        if self._cached_rect == (self.x, self.y, self.width, self.height):
            return
        self._cached_rect = (self.x, self.y, self.width, self.height)
        
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS['card_shadow'])
            RoundedRectangle(pos=(self.x + AppConfig.CARD_ELEVATION, 
                                 self.y - AppConfig.CARD_ELEVATION),
                           size=self.size,
                           radius=[AppConfig.BORDER_RADIUS])
            Color(*COLORS['surface'])
            RoundedRectangle(pos=self.pos, size=self.size,
                           radius=[AppConfig.BORDER_RADIUS])
            Color(*COLORS['card_border'])
            RoundedRectangle(pos=self.pos, size=self.size,
                           radius=[AppConfig.BORDER_RADIUS], line_width=1)

class ModernLabel(Label):
    def __init__(self, variant='primary', **kwargs):
        super().__init__(**kwargs)
        self.halign = 'left'
        self.valign = 'top'
        self.text_size = (None, None)
        
        variant_config = {
            'primary': (COLORS['text_primary'], AppConfig.FONT_SIZE_LARGE, FONT_MEDIUM, True),
            'secondary': (COLORS['text_secondary'], AppConfig.FONT_SIZE_SMALL, FONT_LIGHT, False),
            'header': (COLORS['primary'], AppConfig.FONT_SIZE_HEADER, FONT_MEDIUM, True),
            'success': (COLORS['success'], AppConfig.FONT_SIZE, FONT_MEDIUM, False),
            'error': (COLORS['error'], AppConfig.FONT_SIZE, FONT_MEDIUM, False)
        }
        
        if variant in variant_config:
            self.color, self.font_size, self.font_name, self.bold = variant_config[variant]
        
        self.bind(size=self._update_text_size)
    
    def _update_text_size(self, *args):
        self.text_size = (self.width - AppConfig.PADDING * 2, None)

# Оптимизированный TTS для Android
class TextToSpeech:
    def __init__(self):
        self._lock = threading.Lock()
        self._last_speak_time = 0
        self._min_interval = 2  # Минимальный интервал между озвучиваниями
    
    def speak_text(self, text: str, lang: str = 'ru'):
        if not text or not self._can_speak():
            return
        
        current_time = time.time()
        if current_time - self._last_speak_time < self._min_interval:
            return
        
        self._last_speak_time = current_time
        
        with self._lock:
            try:
                if ANDROID_MEDIA and platform == 'android':
                    # Оптимизированный способ для Android
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                        audio_file = f.name
                    
                    tts = gTTS(text=text, lang=lang, slow=False)
                    tts.save(audio_file)
                    
                    try:
                        media_player = MediaPlayer()
                        media_player.setDataSource(audio_file)
                        media_player.prepare()
                        media_player.start()
                        # Даем время на воспроизведение
                        time.sleep(len(text) * 0.1 + 1)
                        media_player.release()
                    except:
                        pass
                    
                    try:
                        os.unlink(audio_file)
                    except:
                        pass
                elif PLAYSOUND_AVAILABLE:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                        audio_file = f.name
                    tts = gTTS(text=text, lang=lang, slow=False)
                    tts.save(audio_file)
                    playsound(audio_file)
                    try:
                        os.unlink(audio_file)
                    except:
                        pass
            except Exception as e:
                print(f"TTS Error: {e}")
    
    def _can_speak(self):
        current_time = time.time()
        return current_time - self._last_speak_time >= self._min_interval
    
    def stop_speaking(self):
        pass

# Оптимизированный BarcodeReader с кэшированием
class BarcodeReader:
    def __init__(self, tts_callback: Optional[Callable] = None):
        self.tts_callback = tts_callback
        self._last_detection = None
        self._last_detection_time = 0
        self._cooldown = 3
    
    def decode_barcodes(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        result = frame.copy()
        detections = []
        
        try:
            # Уменьшаем разрешение для скорости
            h, w = frame.shape[:2]
            if w > MAX_FRAME_WIDTH:
                scale = MAX_FRAME_WIDTH / w
                new_w = MAX_FRAME_WIDTH
                new_h = int(h * scale)
                small_frame = cv2.resize(frame, (new_w, new_h))
            else:
                small_frame = frame
            
            pil_image = PILImage.fromarray(cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB))
            decoded_objects = zbar_decode(pil_image)
            
            scale_factor = w / small_frame.shape[1] if w > MAX_FRAME_WIDTH else 1
            
            for obj in decoded_objects:
                barcode_data = obj.data.decode('utf-8', errors='ignore')
                barcode_type = obj.type
                
                points = obj.polygon
                if len(points) == 4:
                    pts = np.array([(int(p.x * scale_factor), int(p.y * scale_factor)) 
                                   for p in points], np.int32)
                    pts = pts.reshape((-1, 1, 2))
                    
                    color = tuple(int(c * 255) for c in COLORS['purple'][:3])
                    cv2.polylines(result, [pts], True, color, 2)
                    
                    display_text = f"{barcode_type}"
                    cv2.putText(result, display_text, 
                              (pts[0][0][0], pts[0][0][1] - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                    
                    detections.append({
                        'type': barcode_type,
                        'data': barcode_data,
                        'bbox': obj.rect
                    })
        
        except Exception as e:
            pass
        
        return result, detections
    
    def speak_barcode(self, detections: List[Dict]):
        if not detections or not self.tts_callback:
            return
        
        current_time = time.time()
        if current_time - self._last_detection_time < self._cooldown:
            return
        
        for detection in detections[:1]:
            code_type = detection['type']
            code_data = detection['data']
            
            if code_type == 'QRCODE':
                text = f"QR код: {code_data[:50]}"
            else:
                text = f"Штрих код: {code_data[:50]}"
            
            self._last_detection_time = current_time
            threading.Thread(target=self.tts_callback, args=(text,), daemon=True).start()

# Оптимизированный CurrencyRecognizer
class CurrencyRecognizer:
    CURRENCY_DB = {
        'rub': {
            10: '10 рублей', 50: '50 рублей', 100: '100 рублей',
            200: '200 рублей', 500: '500 рублей', 1000: '1000 рублей',
            2000: '2000 рублей', 5000: '5000 рублей'
        },
        'usd': {
            1: '1 доллар', 2: '2 доллара', 5: '5 долларов',
            10: '10 долларов', 20: '20 долларов', 50: '50 долларов',
            100: '100 долларов'
        },
        'eur': {
            5: '5 евро', 10: '10 евро', 20: '20 евро',
            50: '50 евро', 100: '100 евро', 200: '200 евро',
            500: '500 евро'
        }
    }
    
    def __init__(self, tts_callback: Optional[Callable] = None):
        self.tts_callback = tts_callback
        self.currency_type = 'rub'
        self._last_detection_time = 0
        self._cooldown = 3
    
    def recognize_currency(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        result = frame.copy()
        detections = []
        
        try:
            # Быстрое обнаружение прямоугольников
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, 
                                          cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 5000:  # Минимальная площадь
                    continue
                
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = max(w, h) / min(w, h)
                
                if 1.5 < aspect_ratio < 3.0:
                    # Быстрое определение цвета
                    roi = frame[y:y+h, x:x+w]
                    avg_color = np.mean(roi, axis=(0, 1))
                    
                    nominal = 100  # По умолчанию
                    if self.currency_type == 'rub':
                        if avg_color[2] > 150:
                            nominal = 5000
                        elif avg_color[0] > 150:
                            nominal = 2000
                        elif avg_color[1] > 150:
                            nominal = 100
                        else:
                            nominal = 500
                    
                    display_name = self.CURRENCY_DB.get(self.currency_type, {}).get(nominal, '')
                    if display_name:
                        color = tuple(int(c * 255) for c in COLORS['gold'][:3])
                        cv2.rectangle(result, (x, y), (x + w, y + h), color, 2)
                        cv2.putText(result, display_name, (x, y - 5),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                        
                        detections.append({
                            'currency': self.currency_type,
                            'nominal': nominal,
                            'display_name': display_name
                        })
        
        except Exception as e:
            pass
        
        return result, detections
    
    def set_currency(self, currency_type: str):
        if currency_type in self.CURRENCY_DB:
            self.currency_type = currency_type
    
    def speak_currency(self, detection: Dict):
        if detection and self.tts_callback:
            current_time = time.time()
            if current_time - self._last_detection_time >= self._cooldown:
                self._last_detection_time = current_time
                text = f"Купюра: {detection['display_name']}"
                threading.Thread(target=self.tts_callback, args=(text,), daemon=True).start()

# Оптимизированный ObjectDetector
class ObjectDetector:
    OBJECT_TEMPLATES = {
        'crosswalk': ObjectTemplate('crosswalk', 'Переход', 0.65, (0, 150, 0)),
        'bus_stop': ObjectTemplate('bus_stop', 'Остановка', 0.6, (150, 0, 0)),
        'medical_cross': ObjectTemplate('medical_cross', 'Крест', 0.7, (0, 0, 150))
    }
    
    def __init__(self, tts_callback: Optional[Callable] = None):
        self.templates: Dict[str, np.ndarray] = {}
        self.last_detected: Dict[str, float] = {}
        self.tts_callback = tts_callback
        self.cooldown_time = 5
    
    def load_template(self, name: str, image_path: str) -> bool:
        if name not in self.OBJECT_TEMPLATES:
            return False
        
        try:
            template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if template is not None:
                # Уменьшаем размер шаблона для скорости
                if template.shape[0] > 100 or template.shape[1] > 100:
                    scale = min(100 / template.shape[0], 100 / template.shape[1])
                    new_w = int(template.shape[1] * scale)
                    new_h = int(template.shape[0] * scale)
                    template = cv2.resize(template, (new_w, new_h))
                self.templates[name] = template
                return True
        except:
            pass
        return False
    
    def load_default_templates(self) -> bool:
        if not os.path.exists(AppConfig.TEMPLATES_DIR):
            try:
                os.makedirs(AppConfig.TEMPLATES_DIR)
            except:
                pass
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
        h, w = frame.shape[:2]
        
        # Уменьшаем кадр для детекции
        scale = min(MAX_FRAME_WIDTH / w, MAX_FRAME_HEIGHT / h, 1.0)
        if scale < 1.0:
            small_h, small_w = int(h * scale), int(w * scale)
            small_frame = cv2.resize(frame, (small_w, small_h))
            gray_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        else:
            gray_small = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            scale = 1.0
        
        detections = []
        new_detections = []
        
        for obj_name, template in self.templates.items():
            if gray_small.shape[0] < template.shape[0] or gray_small.shape[1] < template.shape[1]:
                continue
            
            match = cv2.matchTemplate(gray_small, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(match)
            obj_template = self.OBJECT_TEMPLATES.get(obj_name)
            
            if obj_template and max_val > obj_template.threshold:
                # Масштабируем координаты обратно
                x, y = int(max_loc[0] / scale), int(max_loc[1] / scale)
                tw, th = int(template.shape[1] / scale), int(template.shape[0] / scale)
                
                detection = {
                    'name': obj_name,
                    'display_name': obj_template.display_name,
                    'bbox': ((x, y), (x + tw, y + th))
                }
                detections.append(detection)
                
                cv2.rectangle(result, (x, y), (x + tw, y + th), obj_template.color, 2)
                cv2.putText(result, obj_template.display_name, (x, y - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.4, obj_template.color, 1)
                
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
            names = [d['display_name'] for d in detections]
            text = f"Обнаружен {names[0]}" if len(names) == 1 else f"Обнаружены: {', '.join(names)}"
            threading.Thread(target=self.tts_callback, args=(text,), daemon=True).start()

# Оптимизированные вкладки с общим кодом
class BaseTab(TabbedPanelItem):
    def __init__(self, app, tab_text, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.text = tab_text
        self.is_active = False
        self._update_interval = None
    
    def start_camera(self):
        if not self.is_active and hasattr(self, 'update_frame'):
            self.is_active = True
            self._update_interval = Clock.schedule_interval(self.update_frame, AppConfig.FPS)
    
    def stop_camera(self):
        if self.is_active and self._update_interval:
            Clock.unschedule(self._update_interval)
            self.is_active = False
            if hasattr(self, 'image_widget'):
                self.image_widget.texture = None
            self._update_interval = None
    
    def on_leave(self):
        self.stop_camera()

class BarcodeTab(BaseTab):
    def __init__(self, app, **kwargs):
        super().__init__(app, '📱 Коды', **kwargs)
        self.auto_speak = False
        self.last_detection = None
        self._build_ui()
    
    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=AppConfig.PADDING, spacing=AppConfig.SPACING)
        
        # Видео
        video_card = ModernCard(orientation='vertical', size_hint=(1, 0.5))
        self.image_widget = Image(size_hint=(1, 1), keep_ratio=True, allow_stretch=True)
        video_card.add_widget(self.image_widget)
        layout.add_widget(video_card)
        
        # Кнопки
        btn_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(160), spacing=AppConfig.SPACING)
        
        self.camera_btn = StyledToggleButton(text='▶ Камера', size_hint_y=None, height=dp(44))
        self.camera_btn.bind(on_press=self.toggle_camera)
        
        self.scan_btn = StyledButton(text='📷 Сканировать', color_type='purple', size_hint_y=None, height=dp(44))
        self.scan_btn.bind(on_press=self.scan_barcode)
        
        self.auto_btn = StyledToggleButton(text='🎤 Авто', size_hint_y=None, height=dp(44))
        self.auto_btn.bind(on_press=self.toggle_auto)
        
        btn_layout.add_widget(self.camera_btn)
        btn_layout.add_widget(self.scan_btn)
        btn_layout.add_widget(self.auto_btn)
        layout.add_widget(btn_layout)
        
        # Результат
        result_card = ModernCard(orientation='vertical', size_hint=(1, 0.3))
        scroll = ScrollView()
        self.result_label = ModernLabel(
            variant='secondary',
            text='📱 Наведите на код',
            halign='center',
            valign='middle',
            size_hint_y=None
        )
        self.result_label.bind(texture_size=lambda lbl, ts: setattr(lbl, 'height', ts[1]))
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
    
    def update_frame(self, dt):
        frame = self.app.get_current_frame()
        if frame is not None:
            processed, detections = self.app.barcode_reader.decode_barcodes(frame)
            if detections:
                self.last_detection = detections[0]
                self.result_label.text = f"{detections[0]['type']}\n{detections[0]['data'][:50]}"
                self.result_label.color = COLORS['purple']
                if self.auto_speak:
                    self.app.barcode_reader.speak_barcode(detections)
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
        self.result_label.text = f"{detection['type']}\n{detection['data'][:50]}"
        self.result_label.color = COLORS['purple']
    
    def _update_no_result(self):
        self.result_label.text = "❌ Код не найден"
        self.result_label.color = COLORS['error']
    
    def _update_error(self):
        self.result_label.text = "⚠️ Ошибка"
        self.result_label.color = COLORS['error']

class CurrencyTab(BaseTab):
    def __init__(self, app, **kwargs):
        super().__init__(app, '💰 Купюры', **kwargs)
        self.auto_speak = False
        self.last_detection = None
        self._build_ui()
    
    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=AppConfig.PADDING, spacing=AppConfig.SPACING)
        
        video_card = ModernCard(orientation='vertical', size_hint=(1, 0.45))
        self.image_widget = Image(size_hint=(1, 1), keep_ratio=True, allow_stretch=True)
        video_card.add_widget(self.image_widget)
        layout.add_widget(video_card)
        
        # Кнопки
        btn_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(200), spacing=AppConfig.SPACING)
        
        self.camera_btn = StyledToggleButton(text='▶ Камера', size_hint_y=None, height=dp(44))
        self.camera_btn.bind(on_press=self.toggle_camera)
        
        self.recognize_btn = StyledButton(text='💰 Распознать', color_type='gold', size_hint_y=None, height=dp(44))
        self.recognize_btn.bind(on_press=self.recognize_currency)
        
        self.auto_btn = StyledToggleButton(text='🎤 Авто', size_hint_y=None, height=dp(44))
        self.auto_btn.bind(on_press=self.toggle_auto)
        
        # Выбор валюты
        currency_layout = BoxLayout(size_hint_y=None, height=dp(44), spacing=AppConfig.SPACING_SMALL)
        self.rub_btn = StyledToggleButton(text='🇷🇺 RUB', size_hint_x=0.33, height=dp(40))
        self.rub_btn.state = 'down'
        self.rub_btn.bind(on_press=lambda x: self.set_currency('rub'))
        self.usd_btn = StyledToggleButton(text='🇺🇸 USD', size_hint_x=0.33, height=dp(40))
        self.usd_btn.bind(on_press=lambda x: self.set_currency('usd'))
        self.eur_btn = StyledToggleButton(text='🇪🇺 EUR', size_hint_x=0.33, height=dp(40))
        self.eur_btn.bind(on_press=lambda x: self.set_currency('eur'))
        
        currency_layout.add_widget(self.rub_btn)
        currency_layout.add_widget(self.usd_btn)
        currency_layout.add_widget(self.eur_btn)
        
        btn_layout.add_widget(self.camera_btn)
        btn_layout.add_widget(self.recognize_btn)
        btn_layout.add_widget(self.auto_btn)
        btn_layout.add_widget(currency_layout)
        layout.add_widget(btn_layout)
        
        # Результат
        result_card = ModernCard(orientation='vertical', size_hint=(1, 0.3))
        scroll = ScrollView()
        self.result_label = ModernLabel(
            variant='secondary',
            text='💰 Наведите на купюру',
            halign='center',
            valign='middle',
            size_hint_y=None
        )
        self.result_label.bind(texture_size=lambda lbl, ts: setattr(lbl, 'height', ts[1]))
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
    
    def update_frame(self, dt):
        frame = self.app.get_current_frame()
        if frame is not None:
            processed, detections = self.app.currency_recognizer.recognize_currency(frame)
            if detections:
                self.last_detection = detections[0]
                self.result_label.text = f"💰 {detections[0]['display_name']}"
                self.result_label.color = COLORS['gold']
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
        self.result_label.text = "⚠️ Ошибка"
        self.result_label.color = COLORS['error']

class ObjectDetectionTab(BaseTab):
    def __init__(self, app, **kwargs):
        super().__init__(app, '🎯 Детектор', **kwargs)
        self._build_ui()
    
    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=AppConfig.PADDING, spacing=AppConfig.SPACING)
        
        # Информация
        info_card = ModernCard(orientation='vertical', size_hint_y=None, height=dp(70))
        self.info_label = ModernLabel(variant='secondary', text='📁 Загрузите шаблоны', 
                                     halign='center', size_hint_y=None, height=dp(35))
        self.status_label = ModernLabel(variant='success', text='✅ Готов', 
                                       halign='center', size_hint_y=None, height=dp(35))
        info_card.add_widget(self.info_label)
        info_card.add_widget(self.status_label)
        layout.add_widget(info_card)
        
        # Видео
        video_card = ModernCard(orientation='vertical', size_hint=(1, 0.55))
        self.image_widget = Image(size_hint=(1, 1), keep_ratio=True, allow_stretch=True)
        video_card.add_widget(self.image_widget)
        layout.add_widget(video_card)
        
        # Кнопки
        btn_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), spacing=AppConfig.SPACING)
        
        self.btn_load = StyledButton(text='📁 Шаблоны', size_hint_y=None, height=dp(44))
        self.btn_load.bind(on_press=self.app.show_template_loader)
        
        self.btn_camera = StyledToggleButton(text='▶ Камера', size_hint_y=None, height=dp(44))
        self.btn_camera.bind(on_press=self.toggle_camera)
        
        btn_layout.add_widget(self.btn_load)
        btn_layout.add_widget(self.btn_camera)
        layout.add_widget(btn_layout)
        
        self.content = layout
    
    def toggle_camera(self, instance):
        if instance.state == 'down':
            self.start_camera()
            instance.text = '⏹ Стоп'
        else:
            self.stop_camera()
            instance.text = '▶ Камера'
    
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

class OCRTab(BaseTab):
    def __init__(self, app, **kwargs):
        super().__init__(app, '📝 OCR', **kwargs)
        self.last_text = ""
        self.auto_speak = False
        self._build_ui()
    
    def _build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=AppConfig.PADDING, spacing=AppConfig.SPACING)
        
        video_card = ModernCard(orientation='vertical', size_hint=(1, 0.5))
        self.image_widget = Image(size_hint=(1, 1), keep_ratio=True, allow_stretch=True)
        video_card.add_widget(self.image_widget)
        layout.add_widget(video_card)
        
        # Кнопки
        btn_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150), spacing=AppConfig.SPACING)
        
        self.camera_btn = StyledToggleButton(text='▶ Камера', size_hint_y=None, height=dp(44))
        self.camera_btn.bind(on_press=self.toggle_camera)
        
        self.recognize_btn = StyledButton(text='📷 Распознать', size_hint_y=None, height=dp(44))
        self.recognize_btn.bind(on_press=self.capture_and_recognize)
        
        self.auto_btn = StyledToggleButton(text='🎤 Авто', size_hint_y=None, height=dp(44))
        self.auto_btn.bind(on_press=self.toggle_auto)
        
        btn_layout.add_widget(self.camera_btn)
        btn_layout.add_widget(self.recognize_btn)
        btn_layout.add_widget(self.auto_btn)
        layout.add_widget(btn_layout)
        
        # Результат
        result_card = ModernCard(orientation='vertical', size_hint=(1, 0.3))
        scroll = ScrollView()
        self.result_label = ModernLabel(
            variant='secondary',
            text='📄 Текст будет здесь',
            halign='center',
            valign='middle',
            size_hint_y=None
        )
        self.result_label.bind(texture_size=lambda lbl, ts: setattr(lbl, 'height', ts[1]))
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
            # Оптимизация для скорости
            h, w = frame.shape[:2]
            if w > MAX_FRAME_WIDTH:
                scale = MAX_FRAME_WIDTH / w
                new_w = MAX_FRAME_WIDTH
                new_h = int(h * scale)
                frame = cv2.resize(frame, (new_w, new_h))
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            
            results = self.app.reader.readtext(gray, paragraph=True, 
                                             width_ths=0.7, height_ths=0.7)
            texts = [text for (_, text, prob) in results if prob > AppConfig.OCR_CONFIDENCE_THRESHOLD]
            
            if texts:
                result = "📝 " + " ".join(texts)[:200]
                color = COLORS['success']
                if self.auto_speak:
                    threading.Thread(
                        target=self.app.tts.speak_text,
                        args=(f"Текст: {result[2:50]}",),
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

class TemplateLoaderPopup(Popup):
    def __init__(self, detector, callback, **kwargs):
        super().__init__(**kwargs)
        self.detector = detector
        self.callback = callback
        self.title = "📁 Загрузка шаблона"
        self.size_hint = (0.9, 0.8)
        
        layout = BoxLayout(orientation='vertical', padding=AppConfig.PADDING, spacing=AppConfig.SPACING)
        
        title_label = ModernLabel(variant='header', text="Выберите тип:", 
                                 halign='center', size_hint_y=None, height=dp(40))
        layout.add_widget(title_label)
        
        self.type_label = ModernLabel(variant='secondary', text="❌ Не выбран", 
                                     halign='center', size_hint_y=None, height=dp(30))
        layout.add_widget(self.type_label)
        
        # Кнопки выбора
        for obj_id, obj_template in ObjectDetector.OBJECT_TEMPLATES.items():
            btn = StyledButton(text=obj_template.display_name, size_hint_y=None, height=dp(40))
            btn.obj_id = obj_id
            btn.bind(on_press=self.select_type)
            layout.add_widget(btn)
        
        # Файловый выбор
        self.filechooser = FileChooserListView(
            filters=[f'*{ext}' for ext in AppConfig.SUPPORTED_EXTENSIONS],
            size_hint=(1, 0.4)
        )
        layout.add_widget(self.filechooser)
        
        # Кнопки
        btn_layout = BoxLayout(size_hint_y=None, height=dp(48), spacing=AppConfig.SPACING)
        load_btn = StyledButton(text='✅ Загрузить', color_type='success', size_hint_x=0.5)
        load_btn.bind(on_press=self.load_template)
        cancel_btn = StyledButton(text='❌ Отмена', color_type='warning', size_hint_x=0.5)
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_default_tab = False
        self.tab_width = Window.width / 4
        self.tab_height = dp(50)
        
        # Компоненты
        self.tts = TextToSpeech()
        self.detector = ObjectDetector(tts_callback=self.tts.speak_text)
        self.barcode_reader = BarcodeReader(tts_callback=self.tts.speak_text)
        self.currency_recognizer = CurrencyRecognizer(tts_callback=self.tts.speak_text)
        
        # Инициализация EasyOCR в фоне
        self.reader = None
        self._init_ocr()
        
        # Переменные
        self.capture = None
        self.test_mode = False
        self.last_detections = []
        self._frame_lock = threading.Lock()
        self._last_frame = None
        
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
        Clock.schedule_once(lambda dt: self._init_camera(), 0)
        Clock.schedule_once(lambda dt: self._init_templates(), 1)
        
        # Очистка памяти
        Clock.schedule_interval(lambda dt: gc.collect(), 30)
    
    def _init_ocr(self):
        def load_ocr():
            try:
                self.reader = easyocr.Reader(['ru', 'en'], gpu=False)
            except:
                self.reader = None
        
        threading.Thread(target=load_ocr, daemon=True).start()
    
    def _init_camera(self):
        try:
            self.capture = cv2.VideoCapture(AppConfig.CAMERA_ID)
            if platform == 'android':
                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, MAX_FRAME_WIDTH)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, MAX_FRAME_HEIGHT)
                self.capture.set(cv2.CAP_PROP_FPS, 15)
            
            if not self.capture or not self.capture.isOpened():
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
            return np.zeros((MAX_FRAME_HEIGHT, MAX_FRAME_WIDTH, 3), dtype=np.uint8)
        
        if self.capture and self.capture.isOpened():
            ret, frame = self.capture.read()
            if ret:
                with self._frame_lock:
                    self._last_frame = frame
                return frame
        return self._last_frame
    
    @staticmethod
    def display_frame(frame, widget):
        try:
            if frame is None:
                return
            
            h, w = frame.shape[:2]
            if w > MAX_FRAME_WIDTH:
                scale = MAX_FRAME_WIDTH / w
                new_w = MAX_FRAME_WIDTH
                new_h = int(h * scale)
                frame = cv2.resize(frame, (new_w, new_h))
            
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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
    def build(self):
        self.title = "Vision Assist"
        if platform == 'android':
            from android.config import ACTIVE_CLASS_NAME
        return CameraApp()

if __name__ == '__main__':
    print("🎯 Vision Assist для Android")
    print("="*30)
    
    try:
        MainApp().run()
    except Exception as e:
        print(f"❌ Ошибка: {e}")