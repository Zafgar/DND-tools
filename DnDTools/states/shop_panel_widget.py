"""Shop panel widget — lists a Shop's inventory + lets the DM
buy/sell on behalf of the party.

Reads/writes ``Shop`` and ``Campaign.party_gold`` directly. Buying
debits party gold via :func:`data.town_economy.buy_from_shop`;
selling uses :func:`data.town_economy.sell_to_shop`.

Click an inventory row to focus it; "Osta 1" / "Myy 1" buttons fire
the transaction. Status line shows the latest result.
"""
from __future__ import annotations

from typing import Callable, Optional

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data.town_economy import (
    buy_from_shop, sell_to_shop, restock_item,
)


class ShopPanelWidget:
    WIDTH = 480
    ROW_H = 32

    def __init__(self, shop, campaign,
                  on_close: Optional[Callable[[], None]] = None):
        self.shop = shop
        self.campaign = campaign
        self.on_close = on_close
        self.is_open = False
        self.scroll = 0
        self.content_h = 0
        self._row_rects = []
        self.focused_item = None
        self._status = ""

        self.btn_close = Button(0, 0, 50, 24, "Sulje",
                                  self.close,
                                  color=COLORS.get("panel", (60, 60, 80)))
        self.btn_buy = Button(0, 0, 90, 28, "Osta 1",
                                self._buy_one,
                                color=COLORS.get("success", (90, 200, 120)))
        self.btn_sell = Button(0, 0, 90, 28, "Myy 1",
                                 self._sell_one,
                                 color=COLORS.get("warning", (220, 180, 80)))

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def open(self):
        self.is_open = True
        self._status = ""
        self.scroll = 0

    def close(self):
        self.is_open = False
        if self.on_close:
            self.on_close()

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #
    def _party_gold(self) -> float:
        return float(getattr(self.campaign, "party_gold", 0.0) or 0.0)

    def _set_party_gold(self, amount: float):
        self.campaign.party_gold = max(0.0, float(amount))

    def _buy_one(self):
        if self.focused_item is None:
            self._status = "Valitse ensin esine."
            return
        result = buy_from_shop(self.shop, self.focused_item.item_name,
                                 quantity=1, party_gold=self._party_gold())
        if result.success:
            self._set_party_gold(self._party_gold() - result.price_gp)
            self._status = (f"Ostettu {result.item_name} "
                              f"{result.price_gp:.1f} gp:llä")
        else:
            self._status = f"Ei ostettu: {result.reason}"

    def _sell_one(self):
        if self.focused_item is None:
            self._status = "Valitse ensin esine."
            return
        base = (self.focused_item.base_price_gp
                or self.focused_item.current_price_gp
                or 1.0)
        result = sell_to_shop(self.shop,
                                self.focused_item.item_name,
                                quantity=1,
                                base_price_gp=base)
        if result.success:
            self._set_party_gold(self._party_gold() + result.price_gp)
            self._status = (f"Myyty {result.item_name} "
                              f"{result.price_gp:.1f} gp:llä")
        else:
            self._status = f"Ei myyty: {result.reason}"

    # ------------------------------------------------------------------ #
    # Layout
    # ------------------------------------------------------------------ #
    def _rect(self) -> pygame.Rect:
        from states.map_editor import TOP_BAR_H, BOTTOM_BAR_H
        sw = SCREEN_WIDTH
        sh = SCREEN_HEIGHT
        return pygame.Rect(
            sw - self.WIDTH, TOP_BAR_H,
            self.WIDTH, sh - TOP_BAR_H - BOTTOM_BAR_H,
        )

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        rect = self._rect()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not rect.collidepoint(event.pos):
                return False
            for btn in (self.btn_close, self.btn_buy, self.btn_sell):
                if btn.rect.collidepoint(event.pos):
                    btn.handle_event(event)
                    return True
            for r, item in self._row_rects:
                if r.collidepoint(event.pos):
                    self.focused_item = item
                    return True
            return True
        if event.type == pygame.MOUSEWHEEL and rect.collidepoint(
                pygame.mouse.get_pos()):
            max_s = max(0, self.content_h - rect.height + 100)
            self.scroll = max(0, min(self.scroll - event.y * 30, max_s))
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
        return False

    # ------------------------------------------------------------------ #
    # Draw
    # ------------------------------------------------------------------ #
    def draw(self, screen):
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()
        rect = self._rect()
        pygame.draw.rect(screen, COLORS.get("panel_dark",
                                              (32, 32, 40)), rect)
        pygame.draw.line(screen, COLORS.get("border", (80, 80, 100)),
                         (rect.x, rect.y), (rect.x, rect.bottom), 1)

        # Header
        title = self.shop.name
        screen.blit(fonts.body_bold.render(title, True,
                                              COLORS.get("text_bright",
                                                           (240, 240, 240))),
                    (rect.x + 12, rect.y + 8))
        sub = (f"{self.shop.shop_type} · "
                f"kassa {self.shop.gold:.0f} gp · "
                f"party {self._party_gold():.0f} gp")
        screen.blit(fonts.tiny.render(sub, True,
                                          COLORS.get("text_dim",
                                                       (160, 160, 160))),
                    (rect.x + 12, rect.y + 30))

        self.btn_close.rect.x = rect.right - 60
        self.btn_close.rect.y = rect.y + 6
        self.btn_close.draw(screen, mp)

        # Inventory list
        body_top = rect.y + 60
        body_h = rect.bottom - body_top - 90
        body_rect = pygame.Rect(rect.x + 4, body_top,
                                  rect.width - 8, body_h)
        prev_clip = screen.get_clip()
        screen.set_clip(body_rect)
        self._row_rects = []
        y = body_top - self.scroll
        for item in self.shop.inventory:
            row = pygame.Rect(rect.x + 8, y,
                                rect.width - 16, self.ROW_H)
            self._row_rects.append((row, item))
            is_focus = (self.focused_item is item)
            is_hover = row.collidepoint(mp)
            bg = (COLORS.get("accent", (180, 180, 240))
                   if is_focus
                   else COLORS.get("hover", (60, 60, 80))
                   if is_hover
                   else COLORS.get("panel", (40, 40, 50)))
            pygame.draw.rect(screen, bg, row, border_radius=4)
            qty_str = ("∞" if item.quantity == -1
                        else str(item.quantity))
            unit = (item.current_price_gp or item.base_price_gp)
            screen.blit(
                fonts.small_bold.render(
                    item.item_name, True,
                    COLORS.get("text_bright", (240, 240, 240))),
                (row.x + 8, row.y + 4),
            )
            screen.blit(
                fonts.tiny.render(
                    f"{qty_str} kpl · {unit:.0f} gp",
                    True,
                    COLORS.get("text_dim", (160, 160, 160))),
                (row.x + 8, row.y + 18),
            )
            y += self.ROW_H + 4
        if not self.shop.inventory:
            screen.blit(fonts.small.render(
                "(Inventaario tyhjä — käytä Lisää-toimintoa.)", True,
                COLORS.get("text_dim", (160, 160, 160))),
                (rect.x + 12, body_top + 8))
        self.content_h = (y + self.scroll) - body_top
        screen.set_clip(prev_clip)

        # Action row
        self.btn_buy.rect.x = rect.x + 12
        self.btn_buy.rect.y = rect.bottom - 70
        self.btn_buy.draw(screen, mp)
        self.btn_sell.rect.x = rect.x + 110
        self.btn_sell.rect.y = rect.bottom - 70
        self.btn_sell.draw(screen, mp)
        # Status line
        if self._status:
            col = (COLORS.get("warning", (220, 180, 80))
                    if self._status.startswith("Ei ")
                    else COLORS.get("success", (90, 200, 120)))
            screen.blit(fonts.small.render(self._status, True, col),
                        (rect.x + 12, rect.bottom - 30))
