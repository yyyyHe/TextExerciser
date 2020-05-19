# TextExerciser

## About

TextExerciser, TE for short, is an iterative, feedback-driven text input exerciser, which dedicates to generating valid text inputs for Android apps. 

We implement it in python code based on [Uiautomator2](https://github.com/openatx/uiautomator2) and both emulators and physical devices are supported.

It can be used in app testing for bug finding or working together with dynamic analyse tool for sensitive behaviors detection. TextExerciser has following advantages:
* It does not require system modification or app instrumentation
* It can automatically generate text inputs that can satisfy input constraints when exploring the UI of Android apps.



##### Reference
He, Yuyu, Lei Zhang, Zhemin Yang, Yinzhi Cao, Keke Lian, Shuai Li, Wei Yang et al. "TextExerciser: Feedback-driven Text Input Exercising for Android Applications." In the IEEE Symposium on Security and Privacy (Oakland) 2020.


## Device requirements
* Emulator or Phone for running Android apps. Root the device and install [Xposed Module](https://repo.xposed.info/).
* PC for running TE in python. 

## Setup 

##On your PC

1. Install Python3>=3.6 and Java JDK 8. Remeber to add them to your system enviroment `PATH`

2. Install the [Android SDK](http://developer.android.com/sdk/index.html) from [Android Studio](https://developer.android.com/studio/index.html). 

3. Add `platform_tools` directory in Android SDK to your system enviroment `PATH`

4. Clone this repo and install with `pip`

   ```shell
   git clone url
   cd OpenSourceTextExerciser/
   pip install -r requirements.txt
   pip install -e .
   ```

5. Download stanford-parser and stanford-postagger from [Stanford NLP](https://nlp.stanford.edu/software/). Then, unzip the files and put them in the `packages` folder.

##On your phone

6. Install the apps in `assist_apks` 
- Install Xposed-mudules including `GodEye`, `UIAutoFuzzHook`
- Install `Null keyboard` to prevent input keyboard popup
- Install `smsOberserver` to monitor SMS verification code

## Automation 

* Uiautomator2 init

     ```shell
     python -m uiautomator2 init
     ```
  More details can be found in [Uiautomator2.](https://github.com/openatx/uiautomator2)

## Get Started
1. Prepare on your phone
   * Adjust input keyboard of the device to `Null keyboard`
   * Open the `smsOberserver` app
2. Start from your PC
   * If you just run one app in one device, you can use:
     ```shell
     te -a <.apk-file> -d <device-udid>
     ```
   * Or you have multiple emulators, you can use:     
     ```shell
     te -r <folder> -d <udid1 udid2 ...>
     ```
   * You can use `-o` to specify the output folder, and `-t` to limit the duration for testing each app.
     
   * Besides, if you want to receive the verify code, you should rewrite the `config.json` or specify another file using `-j`.
      
   * You can use `te --help` to see some other options .