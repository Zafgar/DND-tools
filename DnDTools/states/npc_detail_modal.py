"""Phase 39 — NPC detail / info card.

Full-screen DM-facing sheet for one NPC. Sections:

  * Portrait + copy-path button.
  * Identity strip (name, race, gender/age, faction, location).
  * Profile text (appearance / personality / backstory / notes).
  * Inventory: legacy free-text list + structured list (letters,
    keys, documents) with [+] add and [×] remove.
  * Organisations the NPC belongs to (clickable chips).
  * NPC↔NPC links with kind + notes; click target to navigate.
  * Reverse links: "Who lists this NPC in their links?"
  * Active quests linking to this NPC.
  * Copy buttons:
    - Copy name to clipboard
    - Copy NPC as markdown to clipboard
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import pygame

from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.components import Button, fonts
from data import npc_directory as npc_dir
from data.world import World


def _copy_to_clipboard(text: str) -> bool:
    """Try pygame.scrap → tkinter → fail silently. Returns True if
    a clipboard handler accepted the text."""
    if not text:
        return False
    try:
        import pygame.scrap as scrap
        if not scrap.get_init():
            scrap.init()
        scrap.put(pygame.SCRAP_TEXT, text.encode("utf-8"))
        return True
    except Exception:
        pass
    try:
        import tkinter as tk
        r = tk.Tk(); r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.update()
        r.destroy()
        return True
    except Exception:
        return False


class NpcDetailModal:
    WIDTH = 940
    HEIGHT = 680

    def __init__(self, world: World, campaign, npc, *,
                  on_close: Optional[Callable[[], None]] = None,
                  on_navigate_npc: Optional[
                      Callable[[str], None]] = None,
                  on_open_org: Optional[
                      Callable[[str], None]] = None):
        self.world = world
        self.campaign = campaign
        self.npc = npc
        self.on_close = on_close
        self.on_navigate_npc = on_navigate_npc
        self.on_open_org = on_open_org
        self.is_open = False
        self.x = (SCREEN_WIDTH - self.WIDTH) // 2
        self.y = (SCREEN_HEIGHT - self.HEIGHT) // 2
        self.scroll = 0
        self._status = ""
        self._status_timer = 0

        # Hit rects per frame
        self._copy_buttons: List[Tuple[pygame.Rect, str, str]] = []
        # (rect, label, text)
        self._link_chips: List[Tuple[pygame.Rect, str]] = []
        self._org_chips: List[Tuple[pygame.Rect, str]] = []
        self._inv_remove_rects: List[Tuple[pygame.Rect, str]] = []
        self._content_height = 0

        # Buttons
        self.btn_close = Button(0, 0, 90, 28, "Sulje",
                                  self._close,
                                  color=COLORS.get("panel",
                                                     (60, 60, 80)))
        self.btn_add_letter = Button(0, 0, 130, 24, "+ Kirje",
                                          lambda: self._add_inv(
                                              "letter"),
                                          color=COLORS.get("legendary",
                                                             (170, 110,
                                                              220)))
        self.btn_add_key = Button(0, 0, 100, 24, "+ Avain",
                                       lambda: self._add_inv("key"),
                                       color=COLORS.get("warning",
                                                          (220, 180,
                                                           80)))
        self.btn_add_doc = Button(0, 0, 110, 24, "+ Dokumentti",
                                       lambda: self._add_inv(
                                           "document"),
                                       color=COLORS.get("accent",
                                                          (110, 130,
                                                           220)))
        self.btn_add_trinket = Button(0, 0, 120, 24, "+ Esine",
                                           lambda: self._add_inv(
                                               "trinket"),
                                           color=COLORS.get("panel",
                                                              (60, 60,
                                                               80)))

    # ------------------------------------------------------------------ #
    def open(self):
        self.is_open = True
        self.scroll = 0

    def _close(self):
        self.is_open = False
        if self.on_close:
            self.on_close()

    def _status_log(self, text: str):
        self._status = text
        self._status_timer = 180

    def _copy(self, text: str, label: str):
        if _copy_to_clipboard(text):
            self._status_log(f"Kopioitu: {label}")
        else:
            self._status_log(f"({label}: leikepöytä ei käytettävissä)")

    def _add_inv(self, kind: str):
        names = {
            "letter": "Sealed Letter",
            "key": "Unmarked Key",
            "document": "Document",
            "trinket": "Curious Trinket",
        }
        name = names.get(kind, "Item")
        # Auto-number duplicates
        existing = {it.get("name") for it
                     in (self.npc.inventory_detailed or [])}
        if name in existing:
            i = 2
            while f"{name} ({i})" in existing:
                i += 1
            name = f"{name} ({i})"
        npc_dir.add_inventory_item(self.npc, name, kind=kind,
                                       description="")
        self._status_log(f"Lisätty: {name}")

    # ------------------------------------------------------------------ #
    def handle_event(self, event) -> bool:
        if not self.is_open:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._close()
            return True
        if event.type == pygame.MOUSEWHEEL:
            max_scroll = max(
                0, self._content_height - (self.HEIGHT - 100))
            self.scroll = max(0, min(max_scroll,
                                        self.scroll - event.y * 30))
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Always-on buttons
            for btn in (self.btn_close, self.btn_add_letter,
                          self.btn_add_key, self.btn_add_doc,
                          self.btn_add_trinket):
                if btn.rect.collidepoint(event.pos):
                    btn.handle_event(event)
                    return True
            # Per-frame buttons
            for rect, label, text in self._copy_buttons:
                if rect.collidepoint(event.pos):
                    self._copy(text, label)
                    return True
            for rect, target_id in self._link_chips:
                if rect.collidepoint(event.pos):
                    if self.on_navigate_npc:
                        self.on_navigate_npc(target_id)
                    return True
            for rect, org_key in self._org_chips:
                if rect.collidepoint(event.pos):
                    if self.on_open_org:
                        self.on_open_org(org_key)
                    return True
            for rect, item_name in self._inv_remove_rects:
                if rect.collidepoint(event.pos):
                    npc_dir.remove_inventory_item(
                        self.npc, item_name)
                    self._status_log(f"Poistettu: {item_name}")
                    return True
            return True
        return False

    # ------------------------------------------------------------------ #
    def draw(self, screen):
        if not self.is_open:
            return
        mp = pygame.mouse.get_pos()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),
                                    pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)
        pygame.draw.rect(screen, COLORS.get("bg_dark", (22, 22, 30)),
                          rect, border_radius=10)
        pygame.draw.rect(screen, COLORS.get("border_light",
                                              (130, 130, 160)),
                          rect, 2, border_radius=10)

        # Reset per-frame click rects
        self._copy_buttons = []
        self._link_chips = []
        self._org_chips = []
        self._inv_remove_rects = []

        # Header strip (fixed)
        self._draw_header(screen, rect)

        # Scrollable body
        body_top = self.y + 130
        body_bottom = self.HEIGHT + self.y - 60
        body = pygame.Rect(self.x + 4, body_top,
                            self.WIDTH - 8, body_bottom - body_top)
        prev = screen.get_clip()
        screen.set_clip(body)
        y = body_top + 8 - self.scroll

        y = self._draw_profile(screen, y)
        y = self._draw_inventory(screen, y)
        y = self._draw_organisations(screen, y)
        y = self._draw_links(screen, y)
        y = self._draw_quests(screen, y)

        self._content_height = (y - (body_top + 8 - self.scroll))
        screen.set_clip(prev)

        # Footer
        if self._status_timer > 0:
            self._status_timer -= 1
            screen.blit(fonts.small.render(
                self._status, True,
                COLORS.get("success", (90, 200, 120))),
                (self.x + 20, self.HEIGHT + self.y - 52))
        self.btn_close.rect.x = rect.right - 110
        self.btn_close.rect.y = rect.bottom - 40
        self.btn_close.draw(screen, mp)

    # ------------------------------------------------------------------ #
    def _draw_header(self, screen, rect):
        n = self.npc
        # Portrait box (left)
        port_box = pygame.Rect(rect.x + 12, rect.y + 12, 100, 100)
        pygame.draw.rect(screen, COLORS.get("panel_dark",
                                              (40, 40, 56)),
                          port_box, border_radius=6)
        portrait_loaded = False
        if n.portrait_path:
            try:
                surf = pygame.image.load(n.portrait_path)
                surf = pygame.transform.smoothscale(
                    surf, (100, 100))
                screen.blit(surf, port_box.topleft)
                portrait_loaded = True
            except Exception:
                portrait_loaded = False
        if not portrait_loaded:
            initials = "".join(
                w[0].upper() for w in (n.name or "?").split()[:2])
            screen.blit(fonts.body_bold.render(
                initials, True,
                COLORS.get("text_bright", (240, 240, 250))),
                (port_box.x + port_box.width // 2 - 12,
                 port_box.y + port_box.height // 2 - 12))
        # Copy portrait path button
        if n.portrait_path:
            copy_btn = pygame.Rect(port_box.right + 6,
                                      port_box.bottom - 24, 26, 22)
            pygame.draw.rect(screen,
                              COLORS.get("legendary",
                                          (170, 110, 220)),
                              copy_btn, border_radius=4)
            screen.blit(fonts.tiny.render(
                "📋", True, (20, 20, 30)),
                (copy_btn.x + 7, copy_btn.y + 4))
            self._copy_buttons.append(
                (copy_btn, "portrait path", n.portrait_path))

        # Identity
        head_x = rect.x + 128
        screen.blit(fonts.body_bold.render(
            n.name or "(no name)", True,
            COLORS.get("text_bright", (240, 240, 250))),
            (head_x, rect.y + 14))
        # Copy name button
        name_w = fonts.body_bold.size(n.name or "")[0]
        copy_name = pygame.Rect(head_x + name_w + 12,
                                  rect.y + 18, 70, 22)
        pygame.draw.rect(screen,
                          COLORS.get("legendary",
                                      (170, 110, 220)),
                          copy_name, border_radius=4)
        screen.blit(fonts.tiny.render(
            "Kopioi", True, (20, 20, 30)),
            (copy_name.x + 16, copy_name.y + 4))
        self._copy_buttons.append((copy_name, "name", n.name))

        # Sub-line
        sub_bits = []
        if n.race:
            sub_bits.append(n.race)
        if n.gender:
            sub_bits.append(n.gender)
        if n.age:
            sub_bits.append(n.age)
        if n.alignment:
            sub_bits.append(n.alignment)
        if sub_bits:
            screen.blit(fonts.small.render(
                "  ·  ".join(sub_bits), True,
                COLORS.get("text_dim", (170, 170, 180))),
                (head_x, rect.y + 42))
        # Faction + occupation + title row
        bits = []
        if n.title:
            bits.append(f"_{n.title}_")
        if n.occupation:
            bits.append(n.occupation)
        if n.faction:
            bits.append(f"Faktio: {n.faction}")
        if bits:
            screen.blit(fonts.small.render(
                "  ·  ".join(bits), True,
                COLORS.get("text_main", (220, 220, 235))),
                (head_x, rect.y + 62))
        # Location
        loc_str = "(no location)"
        if n.location_id and self.world.locations.get(n.location_id):
            loc_str = (f"Sijainti: "
                        f"{self.world.locations[n.location_id].name}")
        screen.blit(fonts.small.render(
            loc_str, True,
            COLORS.get("text_dim", (180, 180, 195))),
            (head_x, rect.y + 82))
        # Copy markdown button
        md_btn = pygame.Rect(head_x, rect.y + 100, 200, 22)
        pygame.draw.rect(screen,
                          COLORS.get("success", (90, 200, 120)),
                          md_btn, border_radius=4)
        screen.blit(fonts.tiny.render(
            "Kopioi koko sheet (markdown)", True, (20, 20, 30)),
            (md_btn.x + 8, md_btn.y + 4))
        md_text = npc_dir.npc_to_markdown(
            self.world, n, campaign=self.campaign)
        self._copy_buttons.append((md_btn, "markdown", md_text))
        # Separator
        pygame.draw.line(
            screen, COLORS.get("border", (60, 60, 80)),
            (rect.x + 12, rect.y + 124),
            (rect.right - 12, rect.y + 124), 1)

    def _draw_profile(self, screen, y):
        n = self.npc
        for label, val in (("Ulkonäkö", n.appearance),
                              ("Persoona", n.personality),
                              ("Tausta", n.backstory),
                              ("DM-muistiinpanot", n.notes)):
            if not val:
                continue
            screen.blit(fonts.small_bold.render(
                f"{label}:", True,
                COLORS.get("text_bright", (240, 240, 250))),
                (self.x + 20, y))
            y += 20
            for line in self._wrap(val, self.WIDTH - 60):
                screen.blit(fonts.small.render(
                    line, True,
                    COLORS.get("text_main", (220, 220, 235))),
                    (self.x + 30, y))
                y += 17
            y += 4
        return y + 6

    def _draw_inventory(self, screen, y):
        n = self.npc
        screen.blit(fonts.small_bold.render(
            "Inventaario:", True,
            COLORS.get("text_bright", (240, 240, 250))),
            (self.x + 20, y))
        # Add-item buttons
        self.btn_add_letter.rect.x = self.x + 150
        self.btn_add_letter.rect.y = y - 2
        self.btn_add_letter.draw(screen, pygame.mouse.get_pos())
        self.btn_add_key.rect.x = self.btn_add_letter.rect.right + 6
        self.btn_add_key.rect.y = y - 2
        self.btn_add_key.draw(screen, pygame.mouse.get_pos())
        self.btn_add_doc.rect.x = self.btn_add_key.rect.right + 6
        self.btn_add_doc.rect.y = y - 2
        self.btn_add_doc.draw(screen, pygame.mouse.get_pos())
        self.btn_add_trinket.rect.x = self.btn_add_doc.rect.right + 6
        self.btn_add_trinket.rect.y = y - 2
        self.btn_add_trinket.draw(screen, pygame.mouse.get_pos())
        y += 30
        # Legacy free-text items
        for item in (n.inventory_items or []):
            screen.blit(fonts.small.render(
                f"  · {item}", True,
                COLORS.get("text_main", (220, 220, 235))),
                (self.x + 30, y))
            y += 18
        # Structured items
        for it in (getattr(n, "inventory_detailed", None) or []):
            name = it.get("name", "(unknown)")
            kind = it.get("kind", "")
            desc = it.get("description", "")
            qty = it.get("quantity", 1)
            row_text = (f"  · [{kind}] {name}"
                         + (f" ×{qty}" if qty > 1 else "")
                         + (f" — {desc}" if desc else ""))
            screen.blit(fonts.small.render(
                row_text, True,
                COLORS.get("text_main", (220, 220, 235))),
                (self.x + 30, y))
            # × remove
            del_btn = pygame.Rect(self.WIDTH + self.x - 60, y - 2,
                                     20, 18)
            pygame.draw.rect(screen,
                              COLORS.get("danger", (220, 100, 90)),
                              del_btn, border_radius=3)
            screen.blit(fonts.tiny.render(
                "×", True, (20, 20, 30)),
                (del_btn.x + 7, del_btn.y + 1))
            self._inv_remove_rects.append((del_btn, name))
            y += 20
        if (not n.inventory_items and
                not getattr(n, "inventory_detailed", None)):
            screen.blit(fonts.tiny.render(
                "(ei tavaroita — lisää nappia klikkaamalla)", True,
                COLORS.get("text_dim", (170, 170, 180))),
                (self.x + 30, y))
            y += 18
        return y + 8

    def _draw_organisations(self, screen, y):
        if self.campaign is None:
            return y
        try:
            from data import organizations as orgs
        except Exception:
            return y
        org_hits = orgs.organisations_for_npc(self.campaign, self.npc.id)
        if not org_hits and self.npc.name:
            org_hits = orgs.organisations_for_npc_name(
                self.campaign, self.npc.name)
        if not org_hits:
            return y
        screen.blit(fonts.small_bold.render(
            f"Organisaatiot ({len(org_hits)}):", True,
            COLORS.get("text_bright", (240, 240, 250))),
            (self.x + 20, y))
        y += 22
        x = self.x + 30
        for o in org_hits:
            m = o.member_for_npc(self.npc.id)
            rank = (o.rank(m.rank_key) if m else None)
            rank_name = (rank.name if rank
                          else (m.rank_key if m else ""))
            label = (f"{o.name}"
                      + (f" — {rank_name}" if rank_name else ""))
            w = fonts.tiny.size(label)[0] + 14
            chip = pygame.Rect(x, y, w, 22)
            pygame.draw.rect(screen, o.color or (160, 160, 160),
                              chip, border_radius=11)
            screen.blit(fonts.tiny.render(label, True, (20, 20, 30)),
                          (chip.x + 7, chip.y + 4))
            self._org_chips.append((chip, o.key))
            x += w + 6
            if x > self.x + self.WIDTH - 30:
                x = self.x + 30
                y += 26
        y += 30
        return y

    def _draw_links(self, screen, y):
        outgoing = npc_dir.npc_links_of(self.world, self.npc.id)
        incoming = npc_dir.npcs_linking_to(self.world, self.npc.id)
        if not outgoing and not incoming:
            return y
        screen.blit(fonts.small_bold.render(
            "Linkit hahmoihin:", True,
            COLORS.get("text_bright", (240, 240, 250))),
            (self.x + 20, y))
        y += 22
        for link in outgoing:
            txt = f"  → [{link['kind']}] {link['target_name']}"
            if link.get("notes"):
                txt += f"  — {link['notes']}"
            w = fonts.small.size(txt)[0] + 8
            chip = pygame.Rect(self.x + 30, y, max(w, 200), 22)
            pygame.draw.rect(screen,
                              COLORS.get("panel_dark", (40, 40, 56)),
                              chip, border_radius=4)
            screen.blit(fonts.small.render(
                txt, True,
                COLORS.get("accent", (140, 200, 240))),
                (chip.x + 4, chip.y + 3))
            self._link_chips.append((chip, link["target_id"]))
            y += 24
        for link in incoming:
            txt = f"  ← [{link['kind']}] {link['source_name']}"
            if link.get("notes"):
                txt += f"  — {link['notes']}"
            w = fonts.small.size(txt)[0] + 8
            chip = pygame.Rect(self.x + 30, y, max(w, 200), 22)
            pygame.draw.rect(screen,
                              COLORS.get("panel_dark", (40, 40, 56)),
                              chip, border_radius=4)
            screen.blit(fonts.small.render(
                txt, True,
                COLORS.get("warning", (220, 180, 80))),
                (chip.x + 4, chip.y + 3))
            self._link_chips.append((chip, link["source_id"]))
            y += 24
        return y + 6

    def _draw_quests(self, screen, y):
        try:
            from data import quest_log as ql
        except Exception:
            return y
        quests = ql.quests_for_npc(self.world, self.npc.id)
        if not quests:
            return y
        screen.blit(fonts.small_bold.render(
            f"Tehtävät ({len(quests)}):", True,
            COLORS.get("text_bright", (240, 240, 250))),
            (self.x + 20, y))
        y += 22
        for q in quests[:8]:
            screen.blit(fonts.small.render(
                f"  · [{q.status}] {q.name}", True,
                COLORS.get("text_main", (220, 220, 235))),
                (self.x + 30, y))
            y += 18
        return y + 6

    # ------------------------------------------------------------------ #
    def _wrap(self, text, max_width):
        font = fonts.small
        words = (text or "").split()
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= max_width:
                cur = test
            else:
                if cur:
                    yield cur
                cur = w
        if cur:
            yield cur
