#TODO Pose analysis - options
#TODO save analysis video, separate overlay? datafile
#TODO layout
# TODO data summary



import flet as ft
from flet import (
    ElevatedButton,
    FilePicker,
    FilePickerResultEvent,
    Page,
    Row,
    Text,
    icons,)
import base64
import cv2
import csv
import numpy as np
import PoseModule3dFlet as pm
detector = pm.poseDetector()

moveFrame=0
moveNumber=0
is_skip=False
is_forward=False
is_rewind=False
playspeed=1
is_paused=True
is_quit=False
is_slider=False
slider_val=0
is_filepicker=False

follower=ft.Ref[ft.Slider]()
refreshed_text=ft.Ref[ft.Text]()
refreshed_frame=ft.Ref[ft.Text]()
min_frame=ft.Ref[ft.Text]()
max_frame=ft.Ref[ft.Text]()
player=ft.Ref[ft.Container]()
Analyze_button=ft.Ref[ft.ElevatedButton]()

holdlist=[]

with open('datafile.csv') as csvfile:
    favourites = csv.reader(csvfile, delimiter=',')
    for row in favourites:
        holdlist.append(row)

videoname='Curtis.MOV'
cap = cv2.VideoCapture(f"PoseVideos/{videoname}")
scale1=0.5
screenHeight=800
scale=scale1*(screenHeight/int(cap.get(4)))
frame_width = int(cap.get(3) * scale)
frame_height = int(cap.get(4) * scale)
canvasSize=(frame_width,frame_height)
imgCanvas = np.zeros((canvasSize[1], canvasSize[0], 3), np.uint8)

video_fps = cap.get(cv2.CAP_PROP_FPS)
length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frame_counter=cap.get(cv2.CAP_PROP_POS_FRAMES)

start=0
end=length
slider_min=0
slider_max=length

VisThresh=0.7
moveThresh = 7
hipThresh = 5
publish='OFF'
pose="ON"
hipTrail='ON'

datalistRangle=[]
datalistLangle=[]
sideL=-10
sideR=120
thenthumbL= thenthumbR=np.array([0, 0, 0, 0, 0])
hipThenL=hipThenR=([0, 0])

signal="lost"

class Countdown(ft.UserControl):
    def __init__(self):
        super().__init__()

    def did_mount(self):
        self.update_timer()

    def update_timer(self):
        global moveFrame
        global frame_counter
        global is_skip
        global is_forward
        global is_rewind
        global playspeed
        global is_quit
        global is_paused
        global is_slider
        global slider_val
        global slider_min
        global slider_max
        global is_filepicker
        cap = cv2.VideoCapture(f'PoseVideos/{videoname}')
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(start))

        while True:
            if frame_counter >= int(end-1) :
                pass
            if is_paused:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_counter))
                pass
            if is_skip:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(float(moveFrame)))
                is_skip=False
            if is_forward:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_counter))
                is_forward=False
            if is_rewind:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_counter))
                is_rewind=False
            if is_slider:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_counter))
                is_slider = False
            if is_filepicker:
                cap.release()
                cap = cv2.VideoCapture(f"PoseVideos/{videoname}")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                is_filepicker = False
            if is_quit:
                #cap.release()
                is_quit=False
                break

            if frame_counter >= int(end-1):
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(end-1))
                refreshed_frame.current.value = int(frame_counter)
                move_slider()
                self.update()
                pass
            else:
                refreshed_frame.current.value = int(frame_counter)
                move_slider()
                _, frame = cap.read()
                frame = cv2.resize(frame, canvasSize)

                imgGray = cv2.cvtColor(imgCanvas, cv2.COLOR_BGR2GRAY)
                _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
                imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
                frame = cv2.bitwise_and(frame, imgInv)
                frame = cv2.bitwise_or(frame, imgCanvas)

                _, im_arr = cv2.imencode('.png', frame)
                im_b64 = base64.b64encode(im_arr)
                self.img.src_base64 = im_b64.decode("utf-8")
                self.update()
                cv2.waitKey(playspeed)
                if publish == "ON":
                    result.write(frame)
                frame_counter = cap.get(cv2.CAP_PROP_POS_FRAMES)

    def skip_key_action(self):  # press key to see next move
        global moveNumber
        global moveFrame
        global is_skip

        if moveNumber == int(len(holdlist)):
            moveNumber = 0
        # # get frame of move
        moveFrame = holdlist[moveNumber]
        moveFrame = moveFrame[1]
        is_skip = True
        print('skip', moveNumber, moveFrame)
        moveNumber = moveNumber + 1

    def forward_key_action(self):
        global frame_counter
        global is_forward
        frame_counter = min(int(frame_counter + (video_fps * 1)), length - 1)
        print(frame_counter)
        is_forward=True

    def rewind_key_action(self):
        global frame_counter
        global is_rewind
        frame_counter = max(0, int(frame_counter - (video_fps * 1)))
        print(frame_counter)
        is_rewind=True

    def slider_action(self):
        global frame_counter
        global is_slider
        global slider_val
        frame_counter = slider_val #slider value
        print(frame_counter)
        is_slider=True

    def quit_key_action(self):
        global is_quit
        is_quit = True

    def pause_key_action(self):
        global is_paused
        is_paused = not is_paused

    def slow_key_action(self):
        global playspeed
        playspeed = 200

    def fast_key_action(self):
        global playspeed
        playspeed = 1

    def normal_key_action(self):
        global playspeed
        playspeed = 80

    def key_action(e: ft.KeyboardEvent):
        r = Countdown()
        if e.key == 'Q':
            r.quit_key_action()
        if e.key == 'A':
            r.rewind_key_action()
        if e.key == 'D':
            r.forward_key_action()
        if e.key == 'W':
            r.skip_key_action()
        if e.key == 'S':
            r.pause_key_action()
        if e.key == 'Z':
            r.slow_key_action()
        if e.key == 'X':
            r.normal_key_action()
        if e.key == 'C':
            r.fast_key_action()
            print('c')
        if e.key == ' ':
            r.pause_key_action()


    def build(self):
        self.img = ft.Image(
            border_radius=ft.border_radius.all(20)
        )
        return self.img

    def will_unmount(self):
        global is_quit
        is_quit=True


class PoseClass(ft.UserControl):
    global frame_counter
    frame_counter=0

    def __init__(self):
        super().__init__()

    def did_mount(self):
        self.player()

    def build(self):
        self.img = ft.Image(
            border_radius=ft.border_radius.all(20)
        )
        return self.img

    # def will_unmount(self):
    #     global is_quit
    #     is_quit=True

    def Pose(self):
        global thenthumbL
        global thenthumbR
        global hipThenL
        global hipThenR
        frame=self.frame
        detector.settings(VisThresh, moveThresh, hipThresh, hipTrail,scale1)
        detector.findPose(frame, False)
        lmList = detector.findPosition(frame, False)
        if len(lmList) != 0:
            signal=='ok'
    #Left
            findAngleL = detector.findAngle('L', frame, imgCanvas)
            angleL1 = findAngleL[0];
            colourLangle = findAngleL[1];

            movementL=detector.movement('L',thenthumbL, hipThenL, hipThenR)
            thenthumbL=movementL[0]
            detector.armCircles(frame_height)
            detector.moveUIL('L')
    #Right
            findAngleR = detector.findAngle('R', frame, imgCanvas)
            angleR1 = findAngleR[0]
            colourRangle = findAngleR[1]
            movementR=detector.movement('R',thenthumbR, hipThenL, hipThenR)
            thenthumbR = movementR[0]
            hipThenL = movementR[1]
            hipThenR = movementR[2]
            detector.armCircles(frame_height)
            detector.moveUIL( 'R')


            # datalistRangle.append(angleR1); datalistLangle.append(angleL1)

        else:
            # signal=="lost"
            thenthumbR=thenthumbL= hipThenL= hipThenR=[0,0]

        self.frame=frame

    def player(self):
        global is_quit
        global frame_counter

        cap = cv2.VideoCapture(f'PoseVideos/{videoname}')
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(start))

        while True:
            if frame_counter >= int(end - 1):
                pass

            if is_quit:
                # cap.release()
                is_quit = False
                break

            if frame_counter >= int(end - 1):
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(end - 1))
                refreshed_frame.current.value = int(frame_counter)
                move_slider()
                self.update()
                pass
            else:
                refreshed_frame.current.value = int(frame_counter)
                move_slider()
                _, frame = cap.read()
                frame = cv2.resize(frame, canvasSize)
                self.frame=frame

                if pose == "ON":
                    self.Pose()
                    frame=self.frame
                imgGray = cv2.cvtColor(imgCanvas, cv2.COLOR_BGR2GRAY)
                _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
                imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
                frame = cv2.bitwise_and(frame, imgInv)
                frame = cv2.bitwise_or(frame, imgCanvas)

                _, im_arr = cv2.imencode('.png', frame)
                im_b64 = base64.b64encode(im_arr)
                self.img.src_base64 = im_b64.decode("utf-8")
                self.update()
                cv2.waitKey(0)
                if publish == "ON":
                    result.write(frame)
                frame_counter = cap.get(cv2.CAP_PROP_POS_FRAMES)


#general functions.........

def slider_changed(e):
    global slider_val
    print(e.control.value)
    slider_val=e.control.value
    c=Countdown()
    c.slider_action()


def pick_files_result(e: FilePickerResultEvent):
    global videoname
    global is_filepicker
    global player
    selected_files.value = (
        ", ".join(map(lambda f: f.name, e.files)) if e.files else "Cancelled!"
    )
    videoname = selected_files.value
    refreshed_text.current.value=videoname
    refreshed_text.current.visible = True
    is_filepicker=True
    player.current.visible = True
    Analyze_button.current.visible=True


pick_files_dialog = FilePicker(on_result=pick_files_result)
selected_files = Text()


# Save file dialog
def save_file_result(e: FilePickerResultEvent):
    save_file_path.value = e.path if e.path else "Cancelled!"
    save_file_path.update()


save_file_dialog = FilePicker(on_result=save_file_result)
save_file_path = Text()


def move_slider():
    follower.current.value = frame_counter
    follower.current.min=slider_min
    follower.current.max = slider_max
    follower_slider.page.update()


def setSlider1(e):
    val=int(e.control.value)
    global start
    global slider_val
    global slider_min
    global is_paused
    slider_val=val
    slider_min=val
    min_frame.current.value = f"Start Frame: {val}"
    c = Countdown()
    c.slider_action()
    is_paused=True



def setSlider2(e):
    val=int(e.control.value)
    global end
    end=val
    global slider_val
    slider_val = val
    global slider_max
    slider_max = val
    max_frame.current.value = f"End Frame: {val}"
    c = Countdown()
    c.slider_action()

def setSliderVis(e):
    global visThresh
    val=e.control.value
    visThresh = val
    print('VisThresh is', visThresh)

if publish=="ON":
    result = cv2.VideoWriter(f"pose_{videoname}.avi",
                             cv2.VideoWriter_fourcc(*'MJPG'),
                             30, canvasSize)

#trackbar....
follower_slider = ft.Container(
    # margin=ft.margin.only(bottom=40),
    content=ft.Row([
                    ft.Text(frame_counter,
                        ref=refreshed_frame,
                        ),
                    ft.Slider(
                        ref=follower,min=slider_min, max=slider_max, value=frame_counter,
                        on_change=lambda e:slider_changed(e),
                        thumb_color='blue',
                    ),
        ],alignment=ft.MainAxisAlignment.SPACE_EVENLY)
)

c=Countdown() #define Class
#movie players and settings..................
section = ft.Container( #preview player and settings
    # margin=ft.margin.only(bottom=40),
    content=ft.Row(vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
        ft.Card(
            elevation=30,
            content=ft.Container(
                ref=player,visible=False,
                bgcolor=ft.colors.WHITE24,
                padding=10,
                border_radius = ft.border_radius.all(20),
                content=ft.Column([
                    Countdown(),
                    follower_slider,
                    ElevatedButton(
                                "Play/Pause (s)",
                                icon=icons.PLAY_ARROW,
                                on_click=lambda _: c.pause_key_action(),
                            ),

                ],horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        ),
       ]))
section2 = ft.Container(
        ft.Card(
            elevation=30,
            content=ft.Container(
                bgcolor=ft.colors.WHITE24,
                padding=10,
                border_radius=ft.border_radius.all(20),
                content=ft.Column(alignment=ft.MainAxisAlignment.START, controls=
                    [
                    ElevatedButton(
                        "Pick file",
                        icon=icons.UPLOAD_FILE,
                        height=100,
                        width=300,
                        on_click=lambda _: pick_files_dialog.pick_files(
                            allow_multiple=False
                        ),
                    ),
                    ft.Text(str(videoname),
                        ref=refreshed_text,visible=False
                    ),
                    ft.Divider(),
                    ft.Slider(
                        min=0, max=length,on_change=lambda e:setSlider1(e)
                    ),
                    ft.Text(f"Start Frame: {start}",ref=min_frame),
                    ft.Divider(),
                    ft.Slider(
                        min=0, max=length, value=length,on_change=lambda e:setSlider2(e)
                    ),
                    ft.Text(f"End Frame:{end}",ref=max_frame),
                    ft.Card(content=ft.Column([
                        ft.Slider(
                            min=0.5, max=1.0,value=0.7,
                            on_change=lambda f: setSliderVis(f.control.value),
                            label= "{value}", divisions=10
                                        ),
                    ])


                    )

                ],horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )


    )

section = ft.Container( #preview player and settings
    # margin=ft.margin.only(bottom=40),
    content=ft.Column(
        controls=[ft.Card(
            ft.Text('Results')


        )



        ]))

def main(page: ft.Page):
    page.overlay.extend([pick_files_dialog, save_file_dialog])
    page.on_keyboard_event = Countdown.key_action

    def route_change(route):
        global pose
        page.views.clear()
        page.views.append(
            ft.View("/",horizontal_alignment = ft.CrossAxisAlignment.CENTER,
                    vertical_alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                 controls=[
                    ElevatedButton(
                        content=Row([
                        ft.Icon(name=icons.GRAPHIC_EQ, scale=3,color="pink"),

                        ft.Text("New Analysis", size=40)],alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                        height=200,
                        width=400,
                        on_click=lambda _: page.go("/settings"),
                    ),
                     ft.Divider(),
                    ElevatedButton(content=Row([
                        ft.Icon(name=icons.GRADING, scale=3, color="pink"),

                        ft.Text("Results", size=40)],spacing=40, alignment=ft.MainAxisAlignment.CENTER),
                        height=200,
                        width=400,
                        on_click=lambda _: page.go("/results"),
                    ),
                ],padding=30

            ))
        if page.route == "/settings":
            pose="OFF"
            page.horizontal_alignment = ft.CrossAxisAlignment.START
            page.vertical_alignment=ft.MainAxisAlignment.START
            page.views.append(
                ft.View(
                    "/settings",horizontal_alignment = ft.CrossAxisAlignment.START,
                    vertical_alignment=ft.MainAxisAlignment.START,
                    controls=[
                        ft.Row([

                        ElevatedButton(
                            "Home",
                            icon=icons.HOME,
                            on_click=lambda _: page.go("/"),
                            height=100, width=200
                        ),
                        # ElevatedButton(
                        #     "Results",
                        #     icon=icons.GRADING,
                        #     on_click=lambda _: page.go("/results"),
                        # ),
                        #     alignment=ft.MainAxisAlignment.CENTER,
                        #     margin=50,


                        ft.Row([
                        section,
                        section2,
                        ElevatedButton(
                                content=ft.Row([

                                    ft.Container(alignment=ft.alignment.center, padding=30,
                                                 content=ft.Icon(name=ft.icons.EQUALIZER, color="pink", scale=3)),

                                    ft.Container(alignment=ft.alignment.center, content=ft.Text(value="Analyze", size=30))],

                                    ),
                                ref=Analyze_button,
                                width=250,
                                height=150,
                                visible=False,
                                on_click=lambda _: page.go("/analyze"),
                            ),
                        ],
                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                        )
                        ])
                        ]))
        if page.route == "/results":
            pose = "OFF"
            page.views.append(
                ft.View(
                    "/results",[
                        ElevatedButton(
                            "Home",
                            icon=icons.HOME,
                            on_click=lambda _: page.go("/"),
                        ),
                    section,
                    ElevatedButton(
                        "Next Move (w)",
                        icon=icons.BACK_HAND,
                        on_click=lambda _: c.skip_key_action(),
                        ),
                    ]
                ))
        if page.route == "/analyze":
            pose = "ON"
            page.views.append(
                ft.View(
                    "/analyze", [Row([
                        ElevatedButton(
                            "Home",
                            icon=icons.HOME,
                            on_click=lambda _: page.go("/"),
                        ),
                        ft.Column([
                        PoseClass(),
                        follower_slider,
                            ])])
                    ]
                ))

    global videoname
    # page.overlay.extend([pick_files_dialog, save_file_dialog])
    # page.on_keyboard_event = Countdown.key_action

    page.padding = 50
    page.window_left = page.window_left+100
    page.theme_mode = ft.ThemeMode.LIGHT
    page.on_route_change = route_change
    page.go(page.route)


if __name__ == '__main__':
    ft.app(target=main)
    cap.release()
    cv2.destroyAllWindows()