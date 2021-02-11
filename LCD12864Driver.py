# encoding=utf-8
import RPi.GPIO as GPIO
import time
from PIL import Image

# Define device connecting pins.
# When using Serial Mode, RS is "CS", R/W is "SID", E is "SCLK"
LCD_RS = 10
LCD_RW = 9
LCD_E = 11

# In serial mode, before the start of the transfer, LCD need to receive 5 "1"s and
# the data of RS, RW and E pin. Then the the transfer will start with high bit of
# the data and 4 "0"s. Then the low bit of data and 4 "0"s.

# Transfer 5 "1" and the data of RW, RS and E pin.
LCD_DAT = '11111010'
LCD_CMD = '11111000'

E_PULSE = 0.0000005
E_DELAY = 0.00000025
LCD_LINE_1 = ('10000000', '10000001', '10000010', '10000011', '10000100', '10000101', '10000110', '10000111')
LCD_LINE_2 = ('10010000', '10010001', '10010010', '10010011', '10010100', '10010101', '10010110', '10010111')
LCD_LINE_3 = ('10001000', '10001001', '10001010', '10001011', '10001100', '10001101', '10001110', '10001111')
LCD_LINE_4 = ('10011000', '10011001', '10011010', '10011011', '10011100', '10011101', '10011110', '10011111')
LCD_IMG_LINE_1 = ('10000000', '10000001', '10000010', '10000011', '10000100', '10000101', '10000110', '10000111')
LCD_IMG_LINE_2 = ('10001000', '10001001', '10001010', '10001011', '10001100', '10001101', '10001110', '10001111')
LCD_IMG_COL = (
    '10000000', '10000001', '10000010', '10000011', '10000100', '10000101', '10000110', '10000111', '10001000',
    '10001001', '10001010', '10001011', '10001100', '10001101', '10001110', '10001111', '10010000', '10010001',
    '10010010',
    '10010011', '10010100', '10010101', '10010110', '10010111', '10011000', '10011001', '10011010', '10011011',
    '10011100',
    '10011101', '10011110', '10011111')

# Define a device constant.
# Some explanation
# LCD12864 has 16 bytes of DDRAM for each row. Every 16x16 pixels in each row were allocated
# with a RAM address and 2 bytes of space. It can display 2 English character, which occupies
# 1 byte(8 bits) of space in binary ASCII code, or 1 Chinese character, which occupies 2 bytes
# (16bits)of space in binary GB2312 code.
LCD_WIDTH = 16

# Define some commonly used instructions.
CLEAR_LCD = '00000001'
OPEN_DISPLAY = '00001111'
CURSOR_OFF = '00001100'
ENTRY_POINT_SET = '00000111'
IMG_DISPLAY_ON = '00110110'
LCD_BASIC_INSTRUCTION = '00110000'
LCD_EXTENDED_INSTRUCTION = '00110100'

# Setup pin
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # Use BCM/BOARD GPIO numbers
GPIO.setup(LCD_RS, GPIO.OUT)  # RS
GPIO.setup(LCD_RW, GPIO.OUT)  # R/W
GPIO.setup(LCD_E, GPIO.OUT)  # E


# A function which used to separate high bit and low bit of a data
def lcd_HLbit(Data, HL):  # HL=True to output high bit, False to output low bit
    HLbitO = ''
    if HL:
        index = 0
        while index < 4:
            HLbitO += Data[index]
            index += 1
    else:
        index = 4
        while index < 8:
            HLbitO += Data[index]
            index += 1
    return HLbitO


# Transfer a bit of data in serial mode.
# Some explanation
# In serial mode, when "SCLK"(E pin) is in high level, data in "SID"(RW) will be read
# When "SCLK"(E pin) is in low level, data in "SID"(RW) will be allowed to change.
# For more details, search the searching engine for its timing chart
def serial_transfer(Data):
    GPIO.output(LCD_RW, Data)
    time.sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_E, False)
    time.sleep(E_DELAY)


def send_data(Data, SyncData):
    # When "CS"(RS) pin is in high level, LCD will be ready for data transfer
    GPIO.output(LCD_RS, True)

    # Transfer 5 "1"s and the data of RS, RW and E pin
    serial_transfer(int(SyncData[0]))
    serial_transfer(int(SyncData[1]))
    serial_transfer(int(SyncData[2]))
    serial_transfer(int(SyncData[3]))
    serial_transfer(int(SyncData[4]))
    serial_transfer(int(SyncData[5]))
    serial_transfer(int(SyncData[6]))
    serial_transfer(int(SyncData[7]))

    # Transfer high bit and 4 "0"s
    HLbitO = lcd_HLbit(Data, True)
    serial_transfer(int(HLbitO[0]))
    serial_transfer(int(HLbitO[1]))
    serial_transfer(int(HLbitO[2]))
    serial_transfer(int(HLbitO[3]))
    serial_transfer(0)
    serial_transfer(0)
    serial_transfer(0)
    serial_transfer(0)

    # Transfer low bit and 4 "0"s
    HLbitO = lcd_HLbit(Data, False)
    serial_transfer(int(HLbitO[0]))
    serial_transfer(int(HLbitO[1]))
    serial_transfer(int(HLbitO[2]))
    serial_transfer(int(HLbitO[3]))
    serial_transfer(0)
    serial_transfer(0)
    serial_transfer(0)
    serial_transfer(0)

    # End of transfer
    GPIO.output(LCD_RS, False)


# Send following instructions to initiate LCD
def lcd_init():
    send_data(LCD_BASIC_INSTRUCTION, LCD_CMD)
    send_data(OPEN_DISPLAY, LCD_CMD)
    send_data(CLEAR_LCD, LCD_CMD)
    send_data(ENTRY_POINT_SET, LCD_CMD)


# A function that translates English characters into binary ASCII code
def ENG2ASCII(ENG_CHR):
    if len('0' + str(bin(ord(ENG_CHR))[2:])) == 8:
        Result = '0' + str(bin(ord(ENG_CHR))[2:])
    else:
        Result = '0' * (8 - len(str(bin(ord(ENG_CHR)))[2:])) + str(bin(ord(ENG_CHR))[2:])
    return Result


# A function that translates Chinese characters into binary GB2312 code
def CHN2GBK(CHN_CHR):
    Result = []
    for i in list(CHN_CHR.encode(encoding='gb2312', errors='strict')):
        Result.append(str(bin(i))[2:])
    return Result


# A function that detects if a character is Chinese character
def is_Chinese(word):
    for ch in word:
        if '\u4e00' <= ch <= '\u9fff':
            return True
    return False


def lcd_display_string(message, line):
    send_data(line, LCD_CMD)

    CHR_index = 0
    ARRAY_index = 0
    TempList = list(message)
    for i in message:
        if is_Chinese(i):
            if CHR_index == 1:
                TempList.insert(ARRAY_index, ' ')
                CHR_index = 0
        else:
            if CHR_index == 0:
                CHR_index += 1
            else:
                CHR_index = 0
        ARRAY_index += 1
    Result = ''
    Counter = 0
    for i in TempList:
        if is_Chinese(i):
            Counter += 2
        else:
            Counter += 1
    for i in range(LCD_WIDTH - Counter):
        TempList.append(' ')
    for i in TempList:
        Result += i
    for i in Result:
        if is_Chinese(i):
            for ch in CHN2GBK(i):
                send_data(ch, LCD_DAT)
        else:
            send_data(ENG2ASCII(i), LCD_DAT)


def lcd_display_image(ImageAddress, Display_Start_Col=0, Display_Start_Line=0, Up_or_Down_Part=False):
    # When error occurs, try to run this function in default.

    # Tip
    # ImageAddress needs to be a picture's address. Display_Start_Col accepts
    # int from 0-31, add one means move the photo down one pixel(from the up
    # most edge(in the upper or downer part of screen).) Display_Start_Line
    # accepts int from 0-7, add one means move photo left from the left most
    # edge of the screen. Up_or_Down_Part accepts boolean, False means display
    # in the upper part of screen, vice versa.

    # Tip
    # If you try to move a image that cannot fill the screen. Some part of
    # image could remain on the screen. Try to write a pure white or pure black
    # image to erase it, or you can just write another image in the area where
    # the remain of preceded image exists.

    send_data(CURSOR_OFF, LCD_CMD)  # Close cursor
    send_data(LCD_EXTENDED_INSTRUCTION, LCD_CMD)  # Switch to extended instruction

    Img = Image.open(ImageAddress, 'r')  # Open Image
    Width = Img.size[0]  # Read width
    Height = Img.size[1]  # Read height
    Binary_Image = ''  # Define a variable to storage image in binary format
    X_index = 0  # Index
    for i in range(Height):  # Read color data line by line, pixel by pixel
        for n in range(Width):
            Color = Img.getpixel((n, i))
            Color_Data_Sum = Color[0] + Color[1] + Color[2]
            if Color_Data_Sum <= 400:  # If color sums up not exceeded some specific value
                Binary_Image = Binary_Image + '0'  # Write "0"
                X_index += 1
                if X_index == Width:  # If a line of number hits the edge of image
                    Binary_Image = Binary_Image + '\n'  # Line feed
                    X_index = 0  # 索引重置
                else:
                    pass
            else:
                X_index += 1
                Binary_Image = Binary_Image + '1'  # If color sums up exceeded some specific value, write "1"
                if X_index == Width:
                    Binary_Image = Binary_Image + '\n'  # If a line of number hits the edge of image, Line feed
                    X_index = 0  # Reset index
                else:
                    pass

    Binary_Image = Binary_Image.split()  # Split data into "list"
    X_index = 0  # Some indexes
    IMG_Y_index = Display_Start_Col - 1
    send_data(LCD_IMG_COL[IMG_Y_index + 1], LCD_CMD)  # Write RAM address
    send_data(LCD_IMG_LINE_1[Display_Start_Line], LCD_CMD)
    DOWN_HALF = Up_or_Down_Part  # Choose lower part of screen or upper part of screen
    Result = ''  # Define a variable to storage processed result
    CUR_COL = 0  # Current column
    for i in Binary_Image:  # For every line in image
        IMG_Y_index += 1
        for y in i:  # For every data in a line
            if (X_index < 8) and (CUR_COL == IMG_Y_index):  # If "result" was not reach the length
                Result += y  # of 8, then keep adding data into it
                X_index += 1
            elif (X_index >= 8) and (CUR_COL == IMG_Y_index):  # If "result" was at the length
                send_data(Result, LCD_DAT)  # of 8, then send result to LCD
                Result = ''
                Result += y
                X_index = 1
            elif (CUR_COL != IMG_Y_index) and (IMG_Y_index < 32):  # If line was changed
                send_data(Result, LCD_DAT)  # then rewrite address and send result to LCD
                Result = ''
                Result += y
                X_index = 1
                CUR_COL = IMG_Y_index  # rewrite address
                send_data(LCD_IMG_COL[IMG_Y_index], LCD_CMD)
                if not DOWN_HALF:
                    send_data(LCD_IMG_LINE_1[Display_Start_Line], LCD_CMD)
                else:
                    send_data(LCD_IMG_LINE_2[Display_Start_Line], LCD_CMD)
            elif (CUR_COL != IMG_Y_index) and (IMG_Y_index == 32):  # If upper screen was full
                send_data(Result, LCD_DAT)  # then write address of lower part of screen in it
                Result = ''
                Result += y
                X_index = 1
                IMG_Y_index = 0
                CUR_COL = IMG_Y_index
                send_data(LCD_IMG_COL[CUR_COL], LCD_CMD)
                send_data(LCD_IMG_LINE_2[Display_Start_Line], LCD_CMD)
                DOWN_HALF = True
    send_data(Result, LCD_DAT)  # Send the last data to LCD
    send_data(IMG_DISPLAY_ON, LCD_CMD)  # Open image display
    send_data(LCD_BASIC_INSTRUCTION, LCD_CMD)  # Switch to basic instruction set


def clear_lcd():
    send_data(CLEAR_LCD, LCD_CMD)


def image_display_off():
    send_data(LCD_EXTENDED_INSTRUCTION, LCD_CMD)
    send_data(LCD_BASIC_INSTRUCTION, LCD_CMD)


lcd_init()
if __name__ == '__main__':  # If running this script along, then run the test program below
    lcd_display_string('即将开始图片测试', LCD_LINE_1[0])
    lcd_display_string('屏幕会空白几秒钟', LCD_LINE_2[0])
    lcd_display_string('请耐心等待', LCD_LINE_3[0])
    lcd_display_string('', LCD_LINE_4[0])
    time.sleep(5)

    lcd_display_string('Photo test is', LCD_LINE_1[0])
    lcd_display_string('about to start.', LCD_LINE_2[0])
    lcd_display_string('Screen will be b', LCD_LINE_3[0])
    lcd_display_string('lank for seconds', LCD_LINE_4[0])
    time.sleep(5)
    clear_lcd()

    lcd_display_image('Clear2.jpg')
    lcd_display_image('Test2.jpg', 0, 2)
    lcd_display_string('', LCD_LINE_1[0])
    lcd_display_string('    非全屏图片  ', LCD_LINE_2[0])
    lcd_display_string(' Non-full screen', LCD_LINE_3[0])
    lcd_display_string('      photo     ', LCD_LINE_4[0])
    time.sleep(5)
    clear_lcd()

    lcd_display_image('Clear2.jpg')
    lcd_display_image('Test.jpg')
    lcd_display_string('', LCD_LINE_1[0])
    lcd_display_string('    全屏图片    ', LCD_LINE_2[0])
    lcd_display_string('   Full screen  ', LCD_LINE_3[0])
    lcd_display_string('      photo     ', LCD_LINE_4[0])
    time.sleep(5)
    clear_lcd()

    image_display_off()
    lcd_display_string('      你好', LCD_LINE_1[0])
    lcd_display_string('     Hello', LCD_LINE_2[0])
    lcd_display_string('      世界', LCD_LINE_3[0])
    lcd_display_string('     World', LCD_LINE_4[0])
    time.sleep(5)

    lcd_display_string('  驱动测试通过  ', LCD_LINE_1[0])
    lcd_display_string('Driver test pass', LCD_LINE_2[0])
    lcd_display_string('  导入并使用吧  ', LCD_LINE_3[0])
    lcd_display_string('   Import&use   ', LCD_LINE_4[0])
    time.sleep(5)

    lcd_display_string('      作者      ', LCD_LINE_1[0])
    lcd_display_string('     Author:    ', LCD_LINE_2[0])
    lcd_display_string('     FelixW     ', LCD_LINE_3[0])
    lcd_display_string('  QQ:642766671  ', LCD_LINE_4[0])
    time.sleep(5)
