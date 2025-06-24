import PySimpleGUI as sg
import ChessLogic as cl
import time
import os
import copy
import threading
import time
import cv2
import sys
from picamera2 import Picamera2 
from libcamera import Transform
import json
import VisionModule as vm
import platform
import ArmControl as ac
import pygame
import pathlib
import serial

try:
    from picamera.array import PiRGBArray
    from picamera2 import PiCamera2
except:
    pass
    
'''
styles:

BlueMono
GreenTan
LightGreen
Black
Dark
'''

#   GLOBAL VARIABLES

CHESS_PATH = 'pieces_images'  # path to the chess pieces
wclock = os.getcwd() + '/interface_images/wclock.png'
bclock = os.getcwd() + '/interface_images/bclock.png'
FENCODE = ""

BLANK = 0  # piece names
PAWNW = 1
KNIGHTW = 2
BISHOPW = 3
ROOKW = 4
QUEENW = 5
KINGW = 6
PAWNB = 7
KNIGHTB = 8
BISHOPB = 9
ROOKB = 10
QUEENB = 11
KINGB = 12

blank = os.path.join(CHESS_PATH, 'blank.png')
bishopB = os.path.join(CHESS_PATH, 'nbishopb.png')
bishopW = os.path.join(CHESS_PATH, 'nbishopw.png')
pawnB = os.path.join(CHESS_PATH, 'npawnb.png')
pawnW = os.path.join(CHESS_PATH, 'npawnw.png')
knightB = os.path.join(CHESS_PATH, 'nknightb.png')
knightW = os.path.join(CHESS_PATH, 'nknightw.png')
rookB = os.path.join(CHESS_PATH, 'nrookb.png')
rookW = os.path.join(CHESS_PATH, 'nrookw.png')
queenB = os.path.join(CHESS_PATH, 'nqueenb.png')
queenW = os.path.join(CHESS_PATH, 'nqueenw.png')
kingB = os.path.join(CHESS_PATH, 'nkingb.png')
kingW = os.path.join(CHESS_PATH, 'nkingw.png')

images = {BISHOPB: bishopB, BISHOPW: bishopW, PAWNB: pawnB, PAWNW: pawnW, KNIGHTB: knightB, KNIGHTW: knightW,
          ROOKB: rookB, ROOKW: rookW, KINGB: kingB, KINGW: kingW, QUEENB: queenB, QUEENW: queenW, BLANK: blank}

wclock = os.getcwd() + '/interface_images/wclock.png'
bclock = os.getcwd() + '/interface_images/bclock.png'
FENCODE = ""

colorTurn = True
graveyard = 'k0'
playerColor = True
playing =  False
blackSquareColor = '#B58863'
whiteSquareColor = '#F0D9B5'
Debug = False
sequence = []
state = "stby"
newGameState = "config"
gameTime = 60.00
whiteSide = 0
route = os.getcwd() + '/'
homography = []
prevIMG = []
chessRoute = ""
detected = True
selectedCam = 0
skillLevel = 10     # Chess engine difficulty level
cap = cv2.VideoCapture()
rotMat = vm.np.zeros((2,2))
physicalParams = {"baseradius": 0.00,
                    "cbFrame": 0.00,
                    "sqSize": 0.00,
                    "cbHeight": 0.00,
                    "pieceHeight": 0.00}
 

def executeMove(move, params, color, homography, cap, selectedCam):
    z = params["cbHeight"] + params["pieceHeight"]
    angles_rest = [60, 180, 5, 100, 10, 20]
    gClose = 45
    gOpen = 90
    goDown = 0.6 * params["pieceHeight"]
    gripState = gOpen
    x, y = 0, 0

    for i in range(0, len(move), 2):
        x0, y0 = x, y
        x, y = ac.CBtoXY((move[i], move[i+1]), params, color)

        angles1 = ac.simple_IK([x, y, z + 1, gripState])
        ac.send_angles_to_arduino(angles1)
        time.sleep(0.8)

        angles2 = ac.simple_IK([x, y, z - 1 - goDown, gripState])
        ac.send_angles_to_arduino(angles2)
        time.sleep(0.8)

        gripState = gClose if ((i // 2) % 2 == 0) else gOpen
        goDown = 0.5 * params["pieceHeight"] if gripState == gClose else 0.6 * params["pieceHeight"]
        angles2[4] = gripState
        ac.send_angles_to_arduino(angles2)
        time.sleep(0.5)

        angles3 = ac.simple_IK([x, y, z + 1, gripState])
        ac.send_angles_to_arduino(angles3)
        time.sleep(0.8)

    ac.send_angles_to_arduino(angles_rest)
    return True

                    
def setup_serial():
    ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    ser.flush()
    
def systemConfig():
    global chessRoute

    if platform.system() == 'Windows':
        chessRoute = "games/stockfishX64.exe"
    elif platform.system() == 'Linux':
        chessRoute = "/usr/games/stockfish"

#   GAME FUNCTIONS

def pcTurn(board,engine):
    global sequence
    global state
    global homography
    global cap
    global selectedCam
    
    command = ""
    pcMove = engine.play(board, cl.chess.engine.Limit(time=1))
    sequence = cl.sequenceGenerator(pcMove.move.uci(), board)
    
    window.FindElement(key = "gameMessage").Update(sequence["type"])
    if sequence["type"] == "White Queen Side Castling" or sequence["type"] == "Black Queen Side Castling":
        command = "q_castling"
    elif sequence["type"] == "White King Side Castling" or sequence["type"] == "Black King Side Castling":
        command = "k_castling"
    elif sequence["type"] == "Capture":
        command = "capture"
    elif sequence["type"] == "Passant":
        command = "passant"
    elif sequence["type"] == "Promotion":
        command = "promotion"
    if command:
        speakThread = threading.Thread(target=speak, args=[command], daemon=True)
        speakThread.start()
        
    command = ""
    executeMove(sequence["seq"], physicalParams, playerColor, homography, cap, selectedCam)
    board.push(pcMove.move)
    updateBoard(sequence, board)
    if board.is_checkmate():
        window.FindElement(key = "robotMessage").Update("CHECKMATE!")
        command = "checkmate"
    elif board.is_check():
        window.FindElement(key = "robotMessage").Update("CHECK!")
        command = "check"
    if command:
        speakThread = threading.Thread(target=speak, args=[command], daemon=True)
        speakThread.start()
    state = "robotMove"
    if board.is_game_over():
        playing = False
        state = "showGameResult"

def startEngine():
    global engine
    global state
    global homography

    engine = cl.chess.engine.SimpleEngine.popen_uci(chessRoute)
    engine.configure({"Skill Level": skillLevel})
    if playerColor == colorTurn:
        state = "playerTurn"
    else:
        state = "pcTurn"

def playerTurn(board, squares):
    print("[INFO] Player turn triggered")
    result = cl.moveAnalysis(squares, board)
    print("[DEBUG] moveAnalysis result:", result)
    piece = ""
    if result:
        if result["type"] == "Promotion":
            while not piece:
                piece = coronationWindow()
            result["move"] += piece
        sequence = cl.sequenceGenerator(result["move"], board)
        print("[INFO] Executing move:", result["move"])
        window.FindElement(key="gameMessage").Update(sequence["type"])
        board.push_uci(result["move"])
        updateBoard(sequence, board)
        return True
    else:
        print("[WARNING] No valid result from moveAnalysis.")
        return False
        

def startGame():
    global gameTime
    window["newGame"].Update(disabled=True)
    window["quit"].Update(disabled=False)
    window["wcount"].Update(time.strftime("%H:%M:%S", time.gmtime(gameTime)))
    window["bcount"].Update(time.strftime("%H:%M:%S", time.gmtime(gameTime)))
    window["clockButton"].Update(image_filename=wclock)
    window["robotMessage"].Update("Good Luck!")
    window["gameMessage"].Update("--")
    
def quitGame():
    try:
        engine.quit()
    except:
        pass



def renderSquare(image, key, location):
    if (location[0] + location[1]) % 2:
        color =  blackSquareColor
    else:
        color = whiteSquareColor
    return sg.Button('', image_filename=image, size=(1, 1),
                          border_width=0, button_color=('white', color),
                          pad=(0, 0), key=key)

def redrawBoard(board):
    columns = 'abcdefgh'
    global playerColor
    if playerColor:
        sq = 63
        for i in range(8):
            window[str(8-i)+"r"].Update("   "+str(8-i))
            window[str(8-i)+"l"].Update(str(8-i)+"   ")
            for j in range(8):
                window[columns[j]+"t"].Update(columns[j])
                window[columns[j]+"b"].Update(columns[j])    
                color = blackSquareColor if (i + 7-j) % 2 else whiteSquareColor
                pieceNum = board.piece_type_at(sq)
                if pieceNum:
                    if not board.color_at(sq):
                        pieceNum += 6
                else:
                    pieceNum = 0
                piece_image = images[pieceNum]
                elem = window[(i, 7-j)]
                elem.Update(button_color=('white', color),
                            image_filename=piece_image, )
                sq -= 1
    else:
        sq = 0
        for i in range(8):
            window[str(8-i)+"r"].Update("   "+str(i+1))
            window[str(8-i)+"l"].Update(str(i+1)+"   ")
            for j in range(8):
                window[columns[j]+"t"].Update(columns[7-j])
                window[columns[j]+"b"].Update(columns[7-j]) 
                color = blackSquareColor if (i + 7-j) % 2 else whiteSquareColor
                pieceNum = board.piece_type_at(sq)
                if pieceNum:
                    if not board.color_at(sq):
                        pieceNum += 6
                else:
                    pieceNum = 0
                piece_image = images[pieceNum]
                elem = window[(i, 7-j)]
                elem.Update(button_color=('white', color),
                            image_filename=piece_image, )
                sq += 1

def updateBoard(move, board):
    global playerColor
    global images
    for cont in range(0,len(move["seq"]),4):
        squareCleared = move["seq"][cont:cont+2]
        squareOcupied = move["seq"][cont+2:cont+4]
        scNum = cl.chess.SQUARE_NAMES.index(squareCleared)
        
        y = cl.chess.square_file(scNum)
        x = 7 - cl.chess.square_rank(scNum)
        color = blackSquareColor if (x + y) % 2 else whiteSquareColor
        if playerColor:
            elem = window[(x, y)]
        else:
            elem = window[(7-x, 7-y)]
        elem.Update(button_color=('white', color),
                    image_filename=blank, )  

        if squareOcupied != graveyard:
            soNum = cl.chess.SQUARE_NAMES.index(squareOcupied)
            pieceNum = board.piece_type_at(soNum)
            if not board.color_at(soNum):
                pieceNum += 6
            y = cl.chess.square_file(soNum)
            x = 7 - cl.chess.square_rank(soNum)
            color = blackSquareColor if (x + y) % 2 else whiteSquareColor
            if playerColor:
                elem = window[(x, y)]
            else:
                elem = window[(7-x, 7-y)]    
            elem.Update(button_color=('white', color),
                        image_filename=images[pieceNum], )         

def sideConfig(): # gameState: sideConfig
    global newGameState
    global state
    global whiteSide
    global prevIMG
    global rotMat
    i = 0

    img = vm.drawQuadrants(prevIMG)
    imgbytes = cv2.imencode('.png', img)[1].tobytes()

    windowName = "Calibration"
    initGame = [[sg.Text('Please select the "white" pieces side', justification='center', pad = (25,(5,15)), font='Any 15')],
                [sg.Image(data=imgbytes, key='boardImg')],
                [sg.Radio('1-2', group_id='grp', default = True,font='Any 14'), sg.Radio('2-3', group_id='grp',font='Any 14'),sg.Radio('4-3', group_id='grp',font='Any 14'), sg.Radio('1-4', group_id='grp',font='Any 14')],
                [sg.Text('_'*30)],
                [sg.Button("Back"), sg.Submit("Play")]]
    newGameWindow = sg.Window(windowName, default_button_element_size=(12,1), auto_size_buttons=False, location = (100,50), icon='interface_images/robot_icon.ico').Layout(initGame) 

    while True:
        button,value = newGameWindow.Read(timeout=100)
        
        if button == "Play":
            newGameState = "initGame"
            while value[i] == False and i<4:
                i+=1
            whiteSide = i
            if whiteSide == 0:
                theta = 90
            elif whiteSide == 1:
                theta = 180
            elif whiteSide == 2:
                theta = -90
            elif  whiteSide == 3:
                theta = 0

            rotMat = vm.findRotation(theta)
            prevIMG = vm.applyRotation(prevIMG,rotMat)
            break
        if button == "Back":
            newGameState = "ocupiedBoard"
            break
        if button in (None, 'Exit'): # MAIN WINDOW
            state = "stby"
            newGameState = "config"
            break   

    newGameWindow.close()

def ocupiedBoard(): # gameState: ocupiedBoard
    global newGameState
    global state
    global selectedCam
    global homography
    global prevIMG

    windowName = "Calibration"
    initGame = [[sg.Text('Place the chess pieces and press Next', justification='center', pad = (25,(5,15)), font='Any 15')],
                [sg.Image(filename='', key='boardVideo')],
                [sg.Text('_'*30)],
                [sg.Button("Back"), sg.Submit("Next")]]
    newGameWindow = sg.Window(windowName, default_button_element_size=(12,1), auto_size_buttons=False, location = (100,50), icon='interface_images/robot_icon.ico').Layout(initGame)  

    while True:
        button,value = newGameWindow.Read(timeout = 10)

        if detected:    
            frame = takePIC()
            prevIMG = vm.applyHomography(frame,homography)
            imgbytes = cv2.imencode('.png', prevIMG)[1].tobytes()
            newGameWindow['boardVideo'].Update(data=imgbytes)

        if button == "Next":
            newGameState = "sideConfig"
            break
        if button == "Back":
            newGameState = "calibration"
            break
        if button in (None, 'Exit'): # MAIN WINDOW
            state = "stby"
            newGameState = "config"
            break   

    newGameWindow.close()

def calibration(): # gameState: calibration
    global newGameState
    global state
    global selectedCam
    global homography
    global detected

    cbPattern = cv2.imread(route+'interface_images/cb_pattern.jpg', cv2.IMREAD_GRAYSCALE)

    windowName = "Camera calibration"
    initGame = [[sg.Text('Please adjust your camera and remove any chess piece', justification='center', pad = (25,(5,15)), font='Any 15', key = "calibrationBoard")],
                [sg.Image(filename='', key='boardVideo')],
                [sg.Text('_'*30)],
                [sg.Button("Back"), sg.Submit("Next")]]
    newGameWindow = sg.Window(windowName, default_button_element_size=(12,1), auto_size_buttons=False, location = (100,50), icon='interface_images/robot_icon.ico').Layout(initGame) 

    while True:
        button,value = newGameWindow.Read(timeout = 10)

        if detected:    
            frame = takePIC()
            imgbytes = cv2.imencode('.png', frame)[1].tobytes()  
            newGameWindow['boardVideo'].Update(data=imgbytes)
            homography = []
            retIMG, homography = vm.findTransformation(frame,cbPattern)
            if retIMG:
                newGameWindow['calibrationBoard'].Update("Camera calibration successful. Please press Next")
            else:
                newGameWindow['calibrationBoard'].Update("Please adjust your camera and remove any chess piece")

        if button == "Next" and retIMG:
            newGameState = "ocupiedBoard"
            break
        if button == "Back":
            if not selectedCam:
                cap.close()
            newGameState = "config"
            break
        if button in (None, 'Exit'):        # MAIN WINDOW
            state = "stby"
            newGameState = "config"
            break   

    newGameWindow.close() 

def newGameWindow (): # gameState: config
    global playerColor
    global gameTime
    global newGameState
    global state
    global detected
    global cap
    global selectedCam
    global skillLevel

    windowName = "Configuration"
    frame_layout = [[sg.Radio('RPi Cam', group_id='grp', default = True, key = "rpicam"), sg.VerticalSeparator(pad=None), sg.Radio('USB0', group_id='grp', key = "usb0"), sg.Radio('USB1', group_id='grp', key = "usb1")]]

    initGame = [[sg.Text('Game Parameters', justification='center', pad = (25,(5,15)), font='Any 15')],
                [sg.CBox('Play as White', key='userWhite', default = playerColor)],
                [sg.Spin([sz for sz in range(1, 300)], initial_value=10, font='Any 11',key='timeInput'),sg.Text('Game time (min)', pad=(0,0))],
                [sg.Combo([sz for sz in range(1, 11)], default_value=10, key="enginelevel"),sg.Text('Engine skill level', pad=(0,0))],
                [sg.Frame('Camera Selection', frame_layout, pad=(0, 10), title_color='white')],
                [sg.Text('_'*30)],
                [sg.Button("Exit"), sg.Submit("Next")]]
    windowNewGame = sg.Window(windowName, default_button_element_size=(12,1), auto_size_buttons=False, icon='interface_images/robot_icon.ico').Layout(initGame)
    while True:
        button,value = windowNewGame.Read()
        if button == "Next":
            if value["rpicam"] == True:
                selectedCam = 0
            elif value["usb0"] == True:
                selectedCam = 1
            elif value["usb1"] == True:
                selectedCam = 2
            cap = initCam(selectedCam)
            if detected:
                newGameState = "calibration"
                playerColor = value["userWhite"]
                skillLevel = value["enginelevel"]*2
                gameTime = float(value["timeInput"]*60)
            break
        if button in (None, 'Exit'): # MAIN WINDOW
            state = "stby"
            break   
    windowNewGame.close() 

def coronationWindow (): # gameState: config
    global playerColor
    pieceSelected = ""
    rook = rookB
    knight = knightB
    bishop = bishopB
    queen = queenB
    if playerColor:
        rook = rookW
        knight = knightW
        bishop = bishopW
        queen = queenW

    windowName = "Promotion"
    pieceSelection = [[sg.Text('Select the piece for promotion', justification='center', pad = (25,(5,15)), font='Any 15')],
                [sg.Button('', image_filename=rook, size=(1, 1),
                          border_width=0, button_color=('white', "brown"),
                          pad=((40,0), 0), key="rook"),sg.Button('', image_filename=knight, size=(1, 1),
                          border_width=0, button_color=('white', "brown"),
                          pad=(0, 0), key="knight"),sg.Button('', image_filename=bishop, size=(1, 1),
                          border_width=0, button_color=('white', "brown"),
                          pad=(0, 0), key="bishop"),sg.Button('', image_filename=queen, size=(1, 1),
                          border_width=0, button_color=('white', "brown"),
                          pad=(0, 0), key="queen")]]
    windowNewGame = sg.Window(windowName, default_button_element_size=(12,1), auto_size_buttons=False, icon='interface_images/robot_icon.ico').Layout(pieceSelection)
    while True:
        button,value = windowNewGame.Read()
        if button == "rook":
            pieceSelected = "r"
            break
        if button == "knight":
            pieceSelected = "k"
            break
        if button == "bishop":
            pieceSelected = "b"
            break
        if button == "queen":
            pieceSelected = "q"
            break
        if button in (None, 'Exit'): # MAIN WINDOW
            break   
    windowNewGame.close() 
    return pieceSelected

def takePIC():  
    global selectedCam
    global cap
    if selectedCam:
        for i in range(5):                    # Clear images stored in buffer
            cap.grab()
        _ , frame =cap.capture_array()                # USB Cam
    else:
       # cap.capture(rawCapture, format="bgr") # RPi Cam
        frame = cap.capture_array()
       # rawCapture.truncate(0)                # Clear the stream in preparation for the next image
    
    return frame

def quitGameWindow():
    global playing
    global window
    global cap

    if not selectedCam:
        cap.close()

    if playing:
        windowName = "Quit Game"
        quitGame = [[sg.Text('Are you sure?', justification='center', size=(30, 1), font='Any 13')],
                    [sg.Submit("Yes", size=(15, 1)), sg.Submit("No", size=(15, 1))]]

        windowNewGame = sg.Window(windowName, default_button_element_size=(12, 1), auto_size_buttons=False,
                                  icon='interface_images/robot_icon.ico').Layout(quitGame)

        while True:
            button, value = windowNewGame.Read()
            if button == "Yes":
                playing = False
                break
            if button in (None, 'Exit', "No"):
                break

        windowNewGame.close()
  
    
def mainBoardLayout():
    # ------ Menu Definition ------ #      
    menu_def = [['&Configuration',["&Dimensions","E&xit"]],      
                ['&Help', 'About'], ]  

    # ------ Layout ------ # 
    # sg.SetOptions(margins=(0,0))
    sg.theme('Dark')
    # Main board display layout
    board_layout = [[sg.T(' '*12)] + [sg.T('{}'.format(a), pad=((0,47),0), font='Any 13', key = a+'t') for a in 'abcdefgh']]
    # Loop though board and create buttons with images
    for i in range(8):
        numberRow = 8-i 
        row = [sg.T(str(numberRow)+'   ', font='Any 13', key = str(numberRow)+"l")]
        for j in range(8):
            row.append(renderSquare(blank, key=(i,j), location=(i,j)))
        row.append(sg.T('   '+str(numberRow), font='Any 13', key = str(numberRow)+"r"))
        board_layout.append(row)
    # Add labels across bottom of board
    board_layout.append([sg.T(' '*12)] + [sg.T('{}'.format(a), pad=((0,47),0), font='Any 13', key = a+'b') for a in 'abcdefgh'])

    frame_layout_game = [
                [sg.Button('---', size=(14, 2), border_width=0,  font=('courier', 16), button_color=('black', "white"), pad=(4, 4), key="gameMessage")],
               ]
    frame_layout_robot = [
                [sg.Button('---', size=(14, 2), border_width=0,  font=('courier', 16), button_color=('black', "white"), pad=(4, 4), key="robotMessage")],
                ]
    board_controls = [[sg.RButton('New Game', key='newGame', size=(15, 2), pad=(0,(0,7)), font=('courier', 16))],
                        [sg.Button('تحكم يدوي', key='manualControl', size=(15, 2), font=('courier', 16))],
                        [sg.RButton('Quit', key='quit', size=(15, 2), pad=(0, 0), font=('courier', 16), disabled = True)],
                        [sg.Frame('GAME', frame_layout_game, pad=(0, 10), font='Any 12', title_color='white', key = "frameMessageGame")],
                        [sg.Frame('ROBOT', frame_layout_robot, pad=(0, (0,10)), font='Any 12', title_color='white', key = "frameMessageRobot")],
                        [sg.Button('White Time', size=(7, 2), border_width=0,  font=('courier', 16), button_color=('black', whiteSquareColor), pad=(0, 0), key="wt"),sg.Button('Black Time',  font=('courier', 16), size=(7, 2), border_width=0, button_color=('black', blackSquareColor), pad=((7,0), 0), key="bt")],
                        [sg.T("00:00:00",size=(9, 2), font=('courier', 13),key="wcount",pad = ((4,0),0)),sg.T("00:00:00",size=(9, 2), pad = (0,0), font=('courier', 13),key="bcount")],
                        [sg.Button('', image_filename=wclock, key='clockButton', pad = ((25,0),0))]]

    layout = [[sg.Menu(menu_def, tearoff=False, key="manubar")], 
                [sg.Column(board_layout),sg.VerticalSeparator(pad=None),sg.Column(board_controls)]]

    return layout

    
    
def initCam(selectedCam):
    global detected
    global rawCapture

    button, value = window.Read(timeout=10)

    if selectedCam:  # USB Cam
        cap = cv2.VideoCapture(selectedCam - 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not cap.isOpened():
            detected = False  
            sg.popup_error('USB Video device not found')
    else:  # RPi Cam using picamera2
        cap = Picamera2()
        cap.preview_configuration.main.size = (640, 480)
        cap.preview_configuration.main.format = "RGB888"
        cap.preview_configuration.transform = Transform(hflip=1, vflip=1)
        cap.configure("preview")
        cap.start()
    
    return cap
    


def loadParams():
    global physicalParams

    if os.path.isfile('params.txt'):
        json_file = open('params.txt')
        physicalParams = json.load(json_file)
        print(json_file)
    else:
        outfile = open('params.txt', 'w')
        json.dump(physicalParams, outfile)

def phisicalConfig ():
    global physicalParams
    
    windowName = "Chessboard parameters"
    robotParamLayout= [[sg.Text('Insert the physical dimensions in inches',justification='center', font='Any 14', pad=(10,10))], 
                       [sg.Spin([sz/100 for sz in range(1, 1000)], initial_value=physicalParams["baseradius"], font='Any 11'),sg.Text('Base Radius', pad=(0,0))],
                        [sg.Spin([sz/100 for sz in range(1, 1000)], initial_value=physicalParams["cbFrame"], font='Any 11'),sg.Text('Chess Board Frame', pad=(0,0))],
                        [sg.Spin([sz/100 for sz in range(1, 1000)], initial_value=physicalParams["sqSize"], font='Any 11'),sg.Text('Square Size', pad=(0,0))],
                        [sg.Spin([sz/100 for sz in range(1, 1000)], initial_value=physicalParams["cbHeight"], font='Any 11'),sg.Text('Chess Board Height', pad=(0,0))],
                        [sg.Spin([sz/100 for sz in range(1, 1000)], initial_value=physicalParams["pieceHeight"], font='Any 11'),sg.Text('Tallest Piece Height', pad=(0,0))],
                        [sg.Text('_'*37)],
                        [sg.Submit("Save",  size=(15, 1)),sg.Submit("Close", size=(15, 1))]]

    while True:
        robotParamWindow = sg.Window(windowName, default_button_element_size=(12,1), auto_size_buttons=False, icon='interface_images/robot_icon.ico').Layout(robotParamLayout)
        button,value = robotParamWindow.Read()
        if button == "Save":
            physicalParams = {"baseradius": float(value[0]),
                    "cbFrame": float(value[1]),
                    "sqSize": float(value[2]),
                    "cbHeight": float(value[3]),
                    "pieceHeight": float(value[4])}
            outfile = open('params.txt', 'w')
            json.dump(physicalParams, outfile)
            break
        if button in (None, 'Close'): # MAIN WINDOW
            break   

    robotParamWindow.close()   

layout = mainBoardLayout()
window = sg.Window('ChessRobot', default_button_element_size=(12,1), auto_size_buttons=False, icon='interface_images/robot_icon.ico').Layout(layout)

def speak(command):
    pygame.mixer.init()
    filePath = str(pathlib.Path().absolute())+"/audio/"
    pygame.mixer.music.load(filePath+command+".mp3")
    pygame.mixer.music.play()


def main():
    global playerColor, state, playing, sequence, newGameState, detected
    global physicalParams, prevIMG, rotMat, homography, colorTurn

    systemConfig()
    loadParams()
    board = cl.chess.Board()
    squares = []
    whiteTime = 0
    blackTime = 0
    refTime = time.time()

    while True:
        button, value = window.Read(timeout=100)

        if button in (None, 'Exit') or value.get("manubar") == "Exit":
            angles_rest = [0, 0, 0, 0, 0, 0]
            ac.send_angles_to_arduino(angles_rest)
            break

        if button == "manualControl":
            manual_control_window()

        if value.get("manubar") == "Dimensions":
            if playing:
                sg.popup("Please, first quit the game")
            else:
                phisicalConfig()

        if button == "newGame":
            if all(physicalParams.values()):
                state = "startMenu"
            else:
                sg.popup_error("Please configure the chess board dimensions first")

        if button == "quit":
            quitGameWindow()
            if not playing:
                state = "showGameResult"

        # انتهاء الوقت
        if playing:
            if whiteTime <= 0:
                playing = False
                state = "showGameResult"
                window["gameMessage"].Update("Time Out\nBlack Wins")
            elif blackTime <= 0:
                playing = False
                state = "showGameResult"
                window["gameMessage"].Update("Time Out\nWhite Wins")

        if state == "stby":
            pass

        elif state == "startMenu":
            if newGameState == "config":
                newGameWindow()
            elif newGameState == "calibration":
                calibration()
            elif newGameState == "ocupiedBoard":
                ocupiedBoard()
            elif newGameState == "sideConfig":
                sideConfig()
            elif newGameState == "initGame":
                playing = True
                newGameState = "config"
                board = cl.chess.Board(FENCODE) if FENCODE else cl.chess.Board()
                colorTurn = board.turn
                startGame()
                whiteTime = blackTime = gameTime
                refTime = time.time()
                threading.Thread(target=startEngine, daemon=True).start()
                speak("good_luck")
                state = "stby"
                redrawBoard(board)

        elif state == "playerTurn":
            if button == "clockButton":
                currentIMG = takePIC()
                curIMG = vm.applyHomography(currentIMG, homography)
                curIMG = vm.applyRotation(curIMG, rotMat)
                squares = vm.findMoves(prevIMG, curIMG)
                if playerTurn(board, squares):
                    state = "pcTurn"
                    if board.is_game_over():
                        playing = False
                        state = "showGameResult"
                else:
                    window["gameMessage"].Update("Invalid move!")
                    speak("invalid_move")
                    state = "playerTurn"

        elif state == "pcTurn":
            window["clockButton"].Update(image_filename=wclock if board.turn else bclock)
            threading.Thread(target=pcTurn, args=(board, engine,), daemon=True).start()
            state = "stby"

        elif state == "robotMove":
            previousIMG = takePIC()
            prevIMG = vm.applyHomography(previousIMG, homography)
            prevIMG = vm.applyRotation(prevIMG, rotMat)
            state = "playerTurn"
            window["robotMessage"].Update("---")
            window["clockButton"].Update(image_filename=wclock if board.turn else bclock)

        elif state == "showGameResult":
            result = board.result()
            msg = "Game Over\n"
            if result == "1-0":
                msg += "White Wins"
            elif result == "0-1":
                msg += "Black Wins"
            elif result == "1/2-1/2":
                msg += "Draw"
            else:
                msg += "Unknown Result"
            window["gameMessage"].Update(msg)
            window["robotMessage"].Update("Goodbye")
            speak("goodbye")
            quitGame()
            state = "stby"

        if playing:
            dt = time.time() - refTime
            refTime = time.time()
            if board.turn:
                whiteTime = max(0, whiteTime - dt)
                window["wcount"].Update(time.strftime("%H:%M:%S", time.gmtime(whiteTime)))
            else:
                blackTime = max(0, blackTime - dt)
                window["bcount"].Update(time.strftime("%H:%M:%S", time.gmtime(blackTime)))

    window.close()


if __name__ == "__main__":main()

