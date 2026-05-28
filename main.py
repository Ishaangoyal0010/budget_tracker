import os
import sys

# Platform detection
IS_ANDROID = 'ANDROID_ARGUMENT' in os.environ

# Import Kivy and KivyMD packages
from kivy.config import Config
# Prevent multi-touch emulation orange circles
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle

# We will import database operations and SMS receiver
from database import (
    init_db, add_transaction, update_merchant_mapping,
    get_recent_transactions, get_pending_mappings, get_category_spending
)
from parser import parse_sms
from sms_receiver import AndroidSMSListener

# Initialize DB on start
init_db()

# Request permissions on Android
def request_android_permissions():
    if IS_ANDROID:
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.RECEIVE_SMS,
                Permission.READ_SMS,
                Permission.POST_NOTIFICATIONS
            ])
        except Exception as e:
            print(f"Error requesting Android permissions: {e}")

class ModernCard(BoxLayout):
    """
    A custom flat card widget with rounded corners and a background color
    to build a premium, glassmorphism-like modern UI.
    """
    def __init__(self, bg_color=[0.15, 0.18, 0.25, 1], radius=15, **kwargs):
        super(ModernCard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.bg_color = bg_color
        self.radius = radius
        self.padding = 15
        self.spacing = 10
        self.bind(size=self._update_background, pos=self._update_background)

    def _update_background(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])

class TrackerApp(App):
    # Dynamic properties to update UI labels automatically
    total_spending = StringProperty("₹0.00")
    pending_count = NumericProperty(0)
    recent_transactions = ListProperty([])
    pending_transactions = ListProperty([])
    category_spending = ListProperty([])

    def build(self):
        self.title = "PennyWise: SMS Expense Tracker"
        
        # Request Android permissions at startup
        request_android_permissions()
        
        # Start SMS Listener
        self.sms_listener = AndroidSMSListener(self.on_new_sms_received)
        
        # Build root layout
        root = BoxLayout(orientation='vertical')
        
        # 1. Header Bar (Vibrant Slate Dark Theme)
        header = BoxLayout(size_hint_y=0.1, padding=[15, 10], spacing=10)
        with header.canvas.before:
            Color(0.08, 0.1, 0.15, 1) # Dark primary color
            RoundedRectangle(pos=header.pos, size=header.size, radius=[0, 0, 0, 0])
            
        app_title = Label(
            text="PennyWise Tracker",
            font_size='22sp',
            bold=True,
            halign='left',
            valign='middle',
            color=[0.0, 0.8, 0.6, 1] # Teal Accent
        )
        app_title.bind(size=app_title.setter('text_size'))
        header.add_widget(app_title)
        
        self.status_label = Label(
            text="Monitoring SMS...",
            font_size='12sp',
            size_hint_x=0.3,
            color=[0.6, 0.6, 0.6, 1],
            halign='right',
            valign='middle'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        header.add_widget(self.status_label)
        root.add_widget(header)
        
        # 2. Main Content Area (Scrollable view containing dashboard widgets)
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=15, spacing=15)
        content.bind(minimum_height=content.setter('height'))
        
        # Card A: Spending Overview Widget
        spending_card = ModernCard(bg_color=[0.11, 0.15, 0.22, 1])
        spending_card.size_hint_y = None
        spending_card.height = 140
        
        spending_card.add_widget(Label(
            text="TOTAL MONTHLY SPEND",
            font_size='12sp',
            color=[0.6, 0.7, 0.8, 1],
            size_hint_y=0.25
        ))
        
        self.total_label = Label(
            text=self.total_spending,
            font_size='36sp',
            bold=True,
            color=[1.0, 1.0, 1.0, 1],
            size_hint_y=0.5
        )
        spending_card.add_widget(self.total_label)
        
        self.pending_alert_label = Label(
            text="0 merchants require categorization",
            font_size='13sp',
            color=[0.9, 0.6, 0.2, 1], # Orange
            size_hint_y=0.25
        )
        spending_card.add_widget(self.pending_alert_label)
        content.add_widget(spending_card)
        
        # Card B: Pending Categorization Queue
        self.mapping_card = ModernCard(bg_color=[0.15, 0.15, 0.2, 1])
        self.mapping_card.size_hint_y = None
        self.mapping_card.height = 180
        self.mapping_card.visible = False
        
        self.mapping_title = Label(
            text="Categorize Unknown Merchant",
            font_size='16sp',
            bold=True,
            color=[0.9, 0.6, 0.2, 1],
            size_hint_y=0.2
        )
        self.mapping_card.add_widget(self.mapping_title)
        
        # Form inputs for categorization
        form_row = BoxLayout(spacing=10, size_hint_y=0.4)
        
        self.rename_input = TextInput(
            hint_text="e.g. Ramesh Kirana Store",
            background_color=[0.2, 0.22, 0.28, 1],
            foreground_color=[1, 1, 1, 1],
            hint_text_color=[0.5, 0.5, 0.5, 1],
            multiline=False,
            padding=[10, 10]
        )
        form_row.add_widget(self.rename_input)
        
        self.category_input = TextInput(
            hint_text="Category (e.g. Grocery, Food)",
            background_color=[0.2, 0.22, 0.28, 1],
            foreground_color=[1, 1, 1, 1],
            hint_text_color=[0.5, 0.5, 0.5, 1],
            multiline=False,
            padding=[10, 10]
        )
        form_row.add_widget(self.category_input)
        self.mapping_card.add_widget(form_row)
        
        # Action buttons
        btn_row = BoxLayout(spacing=10, size_hint_y=0.3)
        save_btn = Button(
            text="Save Mapping",
            background_normal='',
            background_color=[0.0, 0.8, 0.6, 1], # Teal
            color=[1, 1, 1, 1],
            bold=True
        )
        save_btn.bind(on_release=self.save_custom_mapping)
        btn_row.add_widget(save_btn)
        
        skip_btn = Button(
            text="Skip",
            background_normal='',
            background_color=[0.3, 0.3, 0.35, 1],
            color=[1, 1, 1, 1]
        )
        skip_btn.bind(on_release=self.skip_mapping)
        btn_row.add_widget(skip_btn)
        
        self.mapping_card.add_widget(btn_row)
        content.add_widget(self.mapping_card)
        
        # Card C: Recent Transactions List
        tx_card = ModernCard(bg_color=[0.12, 0.14, 0.18, 1])
        tx_card.size_hint_y = None
        tx_card.height = 300
        tx_card.add_widget(Label(
            text="RECENT TRANSACTIONS",
            font_size='13sp',
            bold=True,
            color=[0.5, 0.6, 0.7, 1],
            size_hint_y=0.1
        ))
        
        # Scrollable area inside card
        tx_scroll = ScrollView()
        self.tx_list_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.tx_list_layout.bind(minimum_height=self.tx_list_layout.setter('height'))
        tx_scroll.add_widget(self.tx_list_layout)
        tx_card.add_widget(tx_scroll)
        content.add_widget(tx_card)
        
        # Card D: Simulated SMS Panel (Only shown/needed on local testing PC)
        if not IS_ANDROID:
            sim_card = ModernCard(bg_color=[0.1, 0.12, 0.16, 1])
            sim_card.size_hint_y = None
            sim_card.height = 200
            sim_card.add_widget(Label(
                text="SMS SIMULATOR (TESTING ONLY)",
                font_size='13sp',
                bold=True,
                color=[0.0, 0.8, 0.6, 1],
                size_hint_y=0.15
            ))
            
            self.sim_sms_input = TextInput(
                text="Alert: You've spent Rs. 150.00 at RAMESH KUMAR. Ref: UPI:987654.",
                background_color=[0.18, 0.2, 0.25, 1],
                foreground_color=[1, 1, 1, 1],
                multiline=True,
                size_hint_y=0.5
            )
            sim_card.add_widget(self.sim_sms_input)
            
            sim_btn = Button(
                text="Send Simulated SMS to App",
                background_normal='',
                background_color=[0.5, 0.3, 0.8, 1], # Purple Accent
                bold=True,
                size_hint_y=0.3
            )
            sim_btn.bind(on_release=self.simulate_sms_click)
            sim_card.add_widget(sim_btn)
            content.add_widget(sim_card)
            
        scroll.add_widget(content)
        root.add_widget(scroll)
        
        # Initial UI Update
        self.update_ui()
        
        return root

    def on_new_sms_received(self, sender, sms_body):
        """
        Callback fired whenever the BroadcastReceiver intercepts a transaction SMS.
        """
        # Parse the message
        parsed = parse_sms(sms_body)
        if parsed["success"]:
            # Add to local DB
            is_pending = add_transaction(parsed, sms_body)
            # Update UI on Kivy main thread
            Clock.schedule_once(lambda dt: self.update_ui())

    def update_ui(self):
        """
        Queries database and updates all UI widgets.
        """
        # 1. Update total monthly spending
        spending = get_category_spending()
        total_sum = sum(spending.values())
        self.total_spending = f"₹{total_sum:,.2f}"
        self.total_label.text = self.total_spending
        
        # 2. Check for pending mappings
        pending = get_pending_mappings()
        self.pending_count = len(pending)
        self.pending_alert_label.text = f"{self.pending_count} merchant(s) require categorization"
        
        if self.pending_count > 0:
            self.mapping_card.opacity = 1
            self.mapping_card.disabled = False
            # Load the first pending merchant in the form
            self.current_pending_merchant = pending[0]["raw_merchant"]
            self.mapping_title.text = f"Categorize: '{self.current_pending_merchant}'"
            self.rename_input.text = pending[0]["resolved_merchant"]
            self.category_input.text = ""
        else:
            self.mapping_card.opacity = 0
            self.mapping_card.disabled = True
            
        # 3. Update Recent Transactions scroll list
        txs = get_recent_transactions(limit=15)
        self.tx_list_layout.clear_widgets()
        
        if not txs:
            self.tx_list_layout.add_widget(Label(
                text="No transactions recorded yet.",
                color=[0.5, 0.5, 0.5, 1],
                size_hint_y=None,
                height=40
            ))
        else:
            for tx in txs:
                # Custom box for each transaction list item
                item = BoxLayout(orientation='horizontal', size_hint_y=None, height=60, padding=[10, 5])
                
                # Dynamic background depending on transaction type
                bg_col = [0.15, 0.17, 0.22, 1]
                if tx["is_pending_mapping"] == 1:
                    bg_col = [0.22, 0.18, 0.12, 1] # Warm brownish hint for unrecognized
                    
                with item.canvas.before:
                    Color(*bg_col)
                    RoundedRectangle(pos=item.pos, size=item.size, radius=[8])
                
                # Left Column: Name & Category
                lbl_left = BoxLayout(orientation='vertical')
                lbl_left.add_widget(Label(
                    text=tx["resolved_merchant"],
                    bold=True,
                    halign='left',
                    font_size='14sp',
                    color=[1, 1, 1, 1]
                ))
                lbl_left.add_widget(Label(
                    text=f"{tx['category']} • {tx['timestamp'].split()[0]}",
                    halign='left',
                    font_size='11sp',
                    color=[0.6, 0.6, 0.6, 1]
                ))
                # Set alignment
                for child in lbl_left.children:
                    child.bind(size=child.setter('text_size'))
                item.add_widget(lbl_left)
                
                # Right Column: Amount
                amount_text = f"-₹{tx['amount']:.2f}" if tx['type'] == 'DEBIT' else f"+₹{tx['amount']:.2f}"
                amount_color = [0.9, 0.3, 0.3, 1] if tx['type'] == 'DEBIT' else [0.2, 0.8, 0.4, 1]
                
                lbl_right = Label(
                    text=amount_text,
                    font_size='15sp',
                    bold=True,
                    color=amount_color,
                    halign='right',
                    valign='middle',
                    size_hint_x=0.4
                )
                lbl_right.bind(size=lbl_right.setter('text_size'))
                item.add_widget(lbl_right)
                
                self.tx_list_layout.add_widget(item)

    def save_custom_mapping(self, instance):
        """
        Saves the user's manual mapping back to database.
        """
        if hasattr(self, 'current_pending_merchant') and self.current_pending_merchant:
            custom_name = self.rename_input.text.strip()
            category = self.category_input.text.strip()
            
            if not custom_name:
                custom_name = self.current_pending_merchant
            if not category:
                category = "General"
                
            update_merchant_mapping(self.current_pending_merchant, custom_name, category)
            self.update_ui()

    def skip_mapping(self, instance):
        """
        Temporarily hides the current mapping prompt.
        """
        if hasattr(self, 'current_pending_merchant') and self.current_pending_merchant:
            # Update transaction DB to reset pending state so we skip prompting again
            update_merchant_mapping(self.current_pending_merchant, self.current_pending_merchant, "Uncategorized")
            self.update_ui()

    def simulate_sms_click(self, instance):
        """
        Reads string from text box and delivers it to parser
        """
        sms_text = self.sim_sms_input.text.strip()
        if sms_text:
            self.sms_listener.simulate_incoming_sms("BK-HDFCBK", sms_text)

    def on_stop(self):
        # Clean up listeners to prevent Android background resource leakage
        if hasattr(self, 'sms_listener'):
            self.sms_listener.stop()

if __name__ == '__main__':
    TrackerApp().run()
