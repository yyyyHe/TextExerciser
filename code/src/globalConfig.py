# -*- coding: utf-8 -*-
import os

# Base path
current_folder = os.path.dirname(__file__)

# Account information to receive validation code
EmailHost = None
EmailAddress = None
EmailPwd = None
EmailPort = None
PhoneNumber = None
ReceiveSmsDeviceID = None

# Text_exerciser config
MaxMutateTime = 10
TETimeout = 3600
PageHandlerTimeout = 600
BackFindTimeout = 180
# Mutate prob config
prob_equalitarian = 1 / 3
add_tendency = 3 / 9
sub_tendency = 1 / 9
replace_tendency = 5 / 9
prob_domination = 0

# File path
LogPath = os.path.join(current_folder, '../Log')
UiLogPath = os.path.join(LogPath, 'TELog')
TriggerLogPath = os.path.join(LogPath, 'TriggerLog')
DispatcherLogPath = os.path.join(LogPath, 'DispatcherLog')

# Switch
UseInputDB = True
tcpDumpSwitch = False
translateSwitch = False
TETranslateON = False
TETranslaterServiceUrl = 'translate.google.cn'
UsingZ3 = False

# Logs
ExerciseLogName = 'ExerciseLog.txt'
LukasRawTextLogName = 'LukasRawText.txt'
AlertTextLogName = 'AlertText.txt'
ToastTextLogName = 'ToastText.txt'
AppearTextLogName = 'AppearText.txt'
ChaoticLogName = 'ChaoticLog.txt'
ImprovementLogName = 'ImprovementLog.txt'
RestrLogName = 'RestrLog.txt'
SherlockRawTextLogName = 'SherlockRawText.txt'
Str01LogName = 'Str01Type.txt'
StrMultiLogName = 'StrMultiType.txt'

# Nlp
packages_path = os.path.join(current_folder, '../packages')
from nltk.parse import stanford
STANFORD_PARSER=packages_path+'/stanford-parser-full-2018-10-17/stanford-parser.jar'
STANFORD_MODELS=packages_path+'/stanford-parser-full-2018-10-17/stanford-parser-3.9.2-models.jar'
STANFORD_STRING=packages_path+'/stanford-parser-full-2018-10-17/stanford-parser-3.9.2-models/edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz'
STANFORD_TAGGER = packages_path+"/stanford-postagger-2018-10-16/models/english-bidirectional-distsim.tagger"
STANFORD_TAGGER_JAR = packages_path+"/stanford-postagger-2018-10-16/stanford-postagger.jar"
MODEL_01_PATH = packages_path + "/trained_results_01"
MODEL_MULTI_PATH = packages_path + "/trained_results_multi"
PARSER=stanford.StanfordParser(STANFORD_PARSER,STANFORD_MODELS,STANFORD_STRING)

# Runtime Log mode
Debug = False
OUTPUT_MODE = None
te_logger = None
