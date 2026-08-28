from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class GameAccount(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "啟用"
        SUSPENDED = "suspended", "停權"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="game_account")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_at = models.DateTimeField(null=True, blank=True)


class ExternalIdentity(models.Model):
    account = models.ForeignKey(GameAccount, on_delete=models.CASCADE, related_name="external_identities")
    provider = models.CharField(max_length=32)
    provider_user_id = models.CharField(max_length=255)
    channel_context = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["provider", "provider_user_id", "channel_context"], name="unique_external_identity")]


class Job(models.Model):
    name = models.CharField(max_length=50, unique=True)
    required_level = models.PositiveSmallIntegerField(default=1)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Player(models.Model):
    account = models.OneToOneField(GameAccount, on_delete=models.CASCADE, related_name="player")
    name = models.CharField(max_length=20)
    level = models.PositiveSmallIntegerField(default=1, validators=[MaxValueValidator(99)])
    exp = models.PositiveBigIntegerField(default=0)
    gold = models.PositiveBigIntegerField(default=0)
    hp = models.PositiveIntegerField(default=30)
    mp = models.PositiveIntegerField(default=10)
    max_hp = models.PositiveIntegerField(default=30)
    max_mp = models.PositiveIntegerField(default=10)
    atk = models.PositiveIntegerField(default=8)
    defense = models.PositiveIntegerField(default=3)
    intelligence = models.PositiveIntegerField(default=3)
    magic_defense = models.PositiveIntegerField(default=2)
    agility = models.PositiveIntegerField(default=5)
    critical = models.DecimalField(max_digits=4, decimal_places=3, default=0, validators=[MinValueValidator(0), MaxValueValidator(0.5)])
    job = models.ForeignKey(Job, on_delete=models.PROTECT, related_name="players")
    job_count = models.PositiveSmallIntegerField(default=0)
    last_battle_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class Area(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    required_level = models.PositiveSmallIntegerField(default=1)
    cooldown_seconds = models.PositiveSmallIntegerField(default=3)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Monster(models.Model):
    name = models.CharField(max_length=80, unique=True)
    level = models.PositiveSmallIntegerField(default=1)
    max_hp = models.PositiveIntegerField()
    max_mp = models.PositiveIntegerField(default=0)
    atk = models.PositiveIntegerField()
    defense = models.PositiveIntegerField()
    intelligence = models.PositiveIntegerField(default=0)
    magic_defense = models.PositiveIntegerField(default=0)
    agility = models.PositiveIntegerField(default=0)
    critical = models.DecimalField(max_digits=4, decimal_places=3, default=0, validators=[MinValueValidator(0), MaxValueValidator(0.5)])
    exp_reward = models.PositiveIntegerField()
    gold_min = models.PositiveIntegerField()
    gold_max = models.PositiveIntegerField()

    class Meta:
        constraints = [models.CheckConstraint(check=models.Q(gold_max__gte=models.F("gold_min")), name="monster_gold_range_valid")]

    def __str__(self):
        return self.name


class AreaEncounter(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name="encounters")
    monster = models.ForeignKey(Monster, on_delete=models.CASCADE, related_name="encounters")
    weight = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["area", "monster"], name="unique_area_monster")]


class Item(models.Model):
    class Type(models.TextChoices):
        WEAPON = "weapon", "武器"
        ARMOR = "armor", "防具"
        ACCESSORY = "accessory", "飾品"
        MATERIAL = "material", "材料"

    name = models.CharField(max_length=80, unique=True)
    item_type = models.CharField(max_length=16, choices=Type.choices)
    rarity = models.CharField(max_length=16, default="common")
    weapon_type = models.CharField(max_length=30, blank=True)
    atk_bonus = models.IntegerField(default=0)
    defense_bonus = models.IntegerField(default=0)
    agility_bonus = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class PlayerItem(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="inventory")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["player", "item"], name="unique_player_item")]


class EquipmentSet(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name="equipment")
    weapon = models.ForeignKey(Item, on_delete=models.PROTECT, null=True, blank=True, related_name="weapon_users")
    armor = models.ForeignKey(Item, on_delete=models.PROTECT, null=True, blank=True, related_name="armor_users")
    accessory = models.ForeignKey(Item, on_delete=models.PROTECT, null=True, blank=True, related_name="accessory_users")


class DropEntry(models.Model):
    monster = models.ForeignKey(Monster, on_delete=models.CASCADE, related_name="drops")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    drop_rate = models.DecimalField(max_digits=7, decimal_places=6, validators=[MinValueValidator(0), MaxValueValidator(1)])
    min_quantity = models.PositiveSmallIntegerField(default=1)
    max_quantity = models.PositiveSmallIntegerField(default=1)
    drop_group = models.CharField(max_length=40, blank=True)

    class Meta:
        constraints = [models.CheckConstraint(check=models.Q(max_quantity__gte=models.F("min_quantity")), name="drop_quantity_range_valid")]


class WeaponProficiency(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="proficiencies")
    weapon_type = models.CharField(max_length=30)
    level = models.PositiveSmallIntegerField(default=1)
    exp = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["player", "weapon_type"], name="unique_weapon_proficiency")]


class BattleRecord(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="battles")
    monster_snapshot = models.JSONField()
    result = models.CharField(max_length=8)
    end_reason = models.CharField(max_length=24)
    rounds = models.JSONField()
    rewards = models.JSONField()
    random_seed = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
