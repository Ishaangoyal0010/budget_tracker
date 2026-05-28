# PennyWise: SMS Transaction Tracker

PennyWise is a lightweight, privacy-focused Android application built in Python using **Kivy**. It monitors bank transaction SMS alerts (debited payments, UPI transfers) in real-time, extracts the transaction details, and automatically categorizes them. 

For unrecognized merchants (such as local vendors who receive money in their personal names), it prompts the user with a quick form to label the merchant. Once mapped, PennyWise remembers it forever and auto-categorizes all future transfers to that person.

---

## Folder Structure

* `main.py`: The user interface and main loop. Displays the dashboard and mapping manager.
* `parser.py`: Regular expression rules to parse transaction SMS notifications.
* `database.py`: Local SQLite database storing transaction history and merchant mapping dictionary.
* `sms_receiver.py`: Integrates with Android's Java API (`BroadcastReceiver`) to read incoming SMS text.
* `simulate.py`: Utility script to run the local PC GUI simulator on Windows.
* `buildozer.spec`: Package specification used to compile the application into an APK.
* `.github/workflows/build.yml`: Automated GitHub Action to compile your APK in the cloud.

---

## Step 1: Run and Test Locally (Windows Simulator)

You can run the app directly on your Windows PC to test the parsing and learning engine.

1. **Install Kivy**:
   ```bash
   pip install kivy
   ```
2. **Launch the simulator**:
   ```bash
   python simulate.py
   ```
3. **How to test**:
   * Scroll to the bottom to see the **SMS SIMULATOR** panel.
   * Paste or type a mock UPI SMS (e.g. `Paid Rs.150 to RAMESH KUMAR. Ref: UPI:12345`).
   * Click **Send Simulated SMS to App**.
   * It will appear in the transactions list, and a card will pop up asking you to map `RAMESH KUMAR` (since it's not in the default dictionary).
   * Enter a clean name (e.g. "Ramesh Kirana Store") and a category (e.g. "Groceries"), and hit **Save**.
   * Send the same SMS again—it will now categorize it automatically without asking!

---

## Step 2: Build the APK (Share with Friends)

Since compiling Android apps requires complex SDK/NDK setups, we have provided two options to get your `.apk` file:

### Option A: Free Cloud Build via GitHub Actions (Easiest - 5 mins)
You don't need to install anything on your PC!

1. Create a free GitHub repository (can be **Private** to protect your code).
2. Upload/push all files in this project directory to your repository.
3. Go to the **Actions** tab in your GitHub repository.
4. You will see a workflow called **Build Android APK** running automatically.
5. Once it finishes (takes ~4–5 minutes), click on the completed run.
6. Scroll down to the **Artifacts** section and download the `package` zip file, which contains your compiled `PennyWise.apk`.
7. Share the `.apk` with your friends!

### Option B: Local Compilation via Docker
If you have Docker running locally, you can build it on your PC:
1. Open PowerShell and navigate to the project directory.
2. Run Buildozer using a Docker container:
   ```bash
   docker run --rm -v D:/android_sms_tracker:/home/user/hostdir lead2gold/buildozer:latest android debug
   ```
3. The compiled `.apk` will be output to the `bin/` folder inside your directory.

---

## Step 3: Install on your Android Phone

1. Transfer the `.apk` file to your Android phone (via WhatsApp, Google Drive, or USB).
2. Tap the file to install it.
3. If Android prompts you that installation is blocked from "Unknown Sources", go to **Settings** and toggle **Allow installations from this source**.
4. Open the app and grant the **SMS Receiver** and **Notification** permissions when prompted.
5. Send a test UPI payment to someone, and watch it show up in the app instantly!
