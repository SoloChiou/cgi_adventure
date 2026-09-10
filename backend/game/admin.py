from django.contrib import admin

from .models import (
    Area,
    AreaEncounter,
    BattleRecord,
    DropEntry,
    EquipmentSet,
    ExternalIdentity,
    GameAccount,
    Item,
    Job,
    Monster,
    Player,
    Skill,
    PlayerItem,
    WeaponProficiency,
)


admin.site.register([GameAccount, ExternalIdentity, Player, Job, Skill, Area, AreaEncounter, Monster, Item, PlayerItem, EquipmentSet, DropEntry, WeaponProficiency, BattleRecord])
