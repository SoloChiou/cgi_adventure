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
    PlayerItem,
    WeaponProficiency,
)


admin.site.register([GameAccount, ExternalIdentity, Player, Job, Area, AreaEncounter, Monster, Item, PlayerItem, EquipmentSet, DropEntry, WeaponProficiency, BattleRecord])
