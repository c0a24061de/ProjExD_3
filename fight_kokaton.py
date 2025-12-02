import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100
HEIGHT = 650
NUM_OF_BOMBS = 5

# 画像読み込みエラーを防ぐため、実行ファイルのディレクトリへ移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内にあるかを判定する
    引数 obj_rct: 判定したいRect
    戻り値: (横方向判定結果, 縦方向判定結果) Trueなら画面内
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    delta = {
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)
    imgs = {
        (+5, 0): img,
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),
        (-5, 0): img0,
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),
    }

    def __init__(self, xy: tuple[int, int]):
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとんの画像を切り替え、画面に転送する
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        
        # 移動している場合のみ画像を更新（停止中は直前の画像を維持）
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
        
        screen.blit(self.img, self.rct)


class Beam:
    def __init__(self, bird: "Bird"):
        self.img = pg.image.load(f"fig/beam.png")
        self.rct = self.img.get_rect()
        # こうかとんの中心縦座標、右端横座標からビームを出す
        self.rct.centery = bird.rct.centery
        self.rct.left = bird.rct.right
        self.vx, self.vy = +5, 0

    def update(self, screen: pg.Surface):
        # 画面内にある場合のみ移動と描画
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)


class Bomb:
    def __init__(self, color: tuple[int, int, int], rad: int):
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Score:
    def __init__(self):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.value = 0
        self.img = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = 100, HEIGHT - 50

    def update(self, screen: pg.Surface):
        self.img = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.img, self.rct)


def main(): 
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")

    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    beams = [] 
    score = Score()

    clock = pg.time.Clock()
    tmr = 0

    while True:
        # イベント処理
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))

        screen.blit(bg_img, [0, 0])

        # --- こうかとんと爆弾の衝突 ---
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                bird.change_img(8, screen)
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2 - 150, HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return

        # --- 爆弾とビームの衝突判定 ---
        beams_to_remove = []
        bombs_to_remove = []

        for bomb in bombs:
            for beam in beams:
                if bomb.rct.colliderect(beam.rct):
                    bombs_to_remove.append(bomb)
                    beams_to_remove.append(beam)
                    score.value += 1
                    bird.change_img(6, screen)
                    
                    # この爆弾は撃墜されたので、他のビームとの判定を打ち切る（重複スコア防止）
                    break 

        # 衝突しなかったものだけをリストに残す
        bombs = [b for b in bombs if b not in bombs_to_remove]
        beams = [b for b in beams if b not in beams_to_remove]

        # --- ビームが画面外に出たら削除 ---
        beams = [bm for bm in beams if check_bound(bm.rct) == (True, True)]

        # --- 更新処理 ---
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)

        for bm in beams:
            bm.update(screen)

        for bomb in bombs:
            bomb.update(screen)

        score.update(screen)

        pg.display.update()
        clock.tick(50)
        tmr += 1


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()