import datetime
import logging
import cassiopeia as cass
import sys

from datapipelines import common

from datapipelines.pipelines import DataPipeline
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity

_LOGGER = logging.getLogger(__name__)

from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_REGION
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

DOMAIN = "league_of_legends"

CONF_PLAYERS = "players"

PLAYING = "Playing"
NOT_PLAYING = "not playing"

GAME_WON = "Victory"
GAME_LOST = "Defeat"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_PLAYERS): vol.All(
            cv.ensure_list, [{CONF_NAME: cv.string, CONF_REGION: cv.string}]
        ),
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the api client."""
    cass.apply_settings(
        {
            "global": {"default_region": None, "version_from_match": "patch"},
            "logging": {
                "core": "ERROR",
                "default": "ERROR",
                "print_calls": False,
                "print_riot_api_key": False,
            },
            "pipeline": {
                "DDragon": {},
                "RiotAPI": {},
            },
            "plugins": {},
        }
    )

    try:
        cass.set_riot_api_key(config.get(CONF_API_KEY))
    except:
        _LOGGER.error("league_of_legends sensor failed to load")
        return False
    entities = []
    for account in config.get(CONF_PLAYERS):
        try:
            summoner = cass.get_summoner(name=account["name"], region=account["region"])
        except Exception as e:
            _LOGGER.error(
                "failed setting up league_of_legends sensor for "
                + account["name"]
                + ":"
                + e.__str__
            )
            continue
        _LOGGER.info("got account " + account["name"] + " at " + account["region"])
        entities.append(PlayerSensor(summoner))
    if not entities:
        return
    add_entities(entities, True)


class PlayerSensor(SensorEntity):
    """the player Class."""

    def __init__(self, summoner: cass.Summoner):
        """Initialize the sensor."""
        self._summoner = summoner
        self._solo_queue_rank = None
        self._flex_queue_rank = None
        self._last_game = None
        self._name = None
        self._region = None
        self._level = None
        self._state = None
        self._icon = None
        self._side = None
        self._matchtype = None
        self._teammates = []
        self._champion = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def entity_id(self):
        """Return the entity ID."""
        return f"sensor.lol_{self._name.lower()}".replace(" ", "_")

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def entity_picture(self):
        """icon of the account."""
        return self._icon

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attr = {}
        if self._level is not None:
            attr["level"] = self._level
        if self._region is not None:
            attr["region"] = self._region
        if self._teammates:
            attr["teammates"] = self._teammates
        if self._side is not None:
            attr["side"] = self._side.name
        if self._matchtype is not None:
            attr["matchtype"] = self._matchtype
        if self._champion is not None:
            attr["champion"] = self._champion
        if self._solo_queue_rank is not None:
            attr["solo_queue_rank"] = self._solo_queue_rank
        if self._flex_queue_rank is not None:
            attr["flex_queue_rank"] = self._flex_queue_rank
        if self._last_game is not None:
            attr["last_game"] = self._last_game
        return attr

    def update(self):
        """Update device state."""
        self._name = self._summoner.name
        self._level = self._summoner.level
        self._icon = self._summoner.profile_icon.url
        self._side = None
        self._champion = None
        self._state = NOT_PLAYING
        self._matchtype = None
        self._teammates = []
        self._last_game = None

        try:
            self._solo_queue_rank = (
                str(self._summoner.ranks[cass.data.Queue.ranked_solo_fives])
                .replace("<", "")
                .replace(">", "")
            )
        except Exception as e:
            pass
        try:
            self._flex_queue_rank = (
                str(self._summoner.ranks[cass.data.Queue.ranked_flex_fives])
                .replace("<", "")
                .replace(">", "")
            )
        except:
            pass

        for team in self._summoner.match_history[0].teams:
            if team.participants.contains(self._summoner):
                if team.win:
                    self._last_game = GAME_WON
                else:
                    self._last_game = GAME_LOST

        match = None
        try:
            match = self._summoner.current_match
        except common.NotFoundError:
            pass

        print(self._summoner.match_history)
        if match is not None and match.exists:
            self._state = PLAYING
            self._matchtype = match.queue.name
            for participant in match.participants:
                if participant.summoner == self._summoner:
                    self._side = participant.side
                    self._champion = participant.champion.key
                    self._icon = participant.champion.image.url
                    break

            for participant in match.participants:
                if (
                    participant.side == self._side
                    and participant.summoner != self._summoner
                ):
                    self._teammates.append(participant.summoner.name)
