"""
 * author: AK
 * created on 09-03-2025-17h-57m
 * github: https://github.com/TRC-Loop
 * email: ak@stellar-code.com
 * copyright 2025
"""

import pygame as pg

pg.init(); pg.font.init()

def render_text(text: str, size: int, color: tuple[int,int,int] = (0,0,0), antialias = True):
    font = pg.font.Font(size=size)
    text_surface = font.render(text, antialias, color)
    return text_surface