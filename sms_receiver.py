import os
import sys

# Platform detection
IS_ANDROID = 'ANDROID_ARGUMENT' in os.environ

class AndroidSMSListener:
    def __init__(self, callback_func):
        """
        callback_func should be a function taking (sender, message_body)
        """
        self.callback = callback_func
        self.receiver = None
        self.context = None
        
        if IS_ANDROID:
            self.setup_android_listener()
        else:
            print("Running on non-Android platform. SMS Listener will run in Simulator mode.")

    def setup_android_listener(self):
        try:
            from jnius import autoclass, PythonJavaClass, java_method
            
            # Load Android Java classes
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            self.context = PythonActivity.mActivity
            
            IntentFilter = autoclass('android.content.IntentFilter')
            SmsMessage = autoclass('android.telephony.SmsMessage')
            
            class SMSReceiver(PythonJavaClass):
                __javainterfaces__ = ['android/content/BroadcastReceiver']
                __javacontext__ = 'app'
                
                def __init__(self, callback):
                    super(SMSReceiver, self).__init__()
                    self.callback = callback
                
                @java_method('(Landroid/content/Context;Landroid/content/Intent;)V')
                def onReceive(self, context, intent):
                    action = intent.getAction()
                    if action == "android.provider.Telephony.SMS_RECEIVED":
                        bundle = intent.getExtras()
                        if bundle is not None:
                            # Pdus are raw SMS protocol data units
                            pdusObj = bundle.get("pdus")
                            if pdusObj is not None:
                                # Convert Java array to Python-friendly list
                                pdus = pdusObj.toArray() if hasattr(pdusObj, "toArray") else pdusObj
                                
                                for pdu in pdus:
                                    # Create SmsMessage from the pdu
                                    # For newer Android versions, createFromPdu requires a format parameter,
                                    # but we can call it using standard createFromPdu(pdu) fallback
                                    try:
                                        format = bundle.getString("format")
                                        sms = SmsMessage.createFromPdu(pdu, format)
                                    except Exception:
                                        sms = SmsMessage.createFromPdu(pdu)
                                        
                                    sender = sms.getOriginatingAddress()
                                    body = sms.getMessageBody()
                                    
                                    # Trigger the Python callback
                                    self.callback(sender, body)
            
            # Store instance and register the broadcast receiver
            self.receiver = SMSReceiver(self.callback)
            filter = IntentFilter("android.provider.Telephony.SMS_RECEIVED")
            self.context.registerReceiver(self.receiver, filter)
            print("Successfully registered Android SMS BroadcastReceiver!")
            
        except Exception as e:
            print(f"Error setting up Android SMS Listener: {e}")

    def stop(self):
        """
        Unregisters the receiver when app closes to prevent memory leaks.
        """
        if IS_ANDROID and self.context and self.receiver:
            try:
                self.context.unregisterReceiver(self.receiver)
                print("Unregistered Android SMS BroadcastReceiver.")
            except Exception as e:
                print(f"Error unregistering receiver: {e}")

    def simulate_incoming_sms(self, sender, body):
        """
        Allows simulating SMS delivery on PC/Windows.
        """
        if not IS_ANDROID:
            print(f"\n[SIMULATED SMS] From: {sender} | Content: {body}")
            self.callback(sender, body)
