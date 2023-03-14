#include <string>
#include <iostream>

std::string generateDateFormat(esphome::time::ESPTime time, std::string nameday) {
  std::string months[12] = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"};
  std::string weekdays[7] = {"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"};
  std::string dateFormat = months[atoi(time.strftime("%m").c_str()) - 1] + std::string(" %d, ") + weekdays[atoi(time.strftime("%w").c_str())] + " | " + nameday;
  return dateFormat;
}

#define ICON_stop "\U000F04DB"
#define ICON_play "\U000F040A"
#define ICON_pause "\U000F03E4"

std::string playbackStatusToIcon(bool playing, bool paused) {
  if (playing) return ICON_play;
  else if (paused) return ICON_pause;
  else return ICON_stop;
}

#define ICON_w_clear_night "\U000F0594"
#define ICON_w_cloudy "\U000F0590"
#define ICON_w_fog "\U000F0591"
#define ICON_w_hail "\U000F0592"
#define ICON_w_lightning "\U000F0593"
#define ICON_w_lightning_rainy "\U000F067E"
#define ICON_w_night_partly_cloudy "\U000F0F31"
#define ICON_w_partly_cloudy "\U000F0595"
#define ICON_w_pouring "\U000F0596"
#define ICON_w_rainy "\U000F0597"
#define ICON_w_snowy "\U000F0F36"
#define ICON_w_snowy_rainy "\U000F067F"
#define ICON_w_sunny "\U000F0599"
#define ICON_w_windy "\U000F059D"
#define ICON_w_windy_variant "\U000F059E"
#define ICON_w_exceptional "\U000F0F38"
#define ICON_storm "\U000F0593"

std::string conditionToIcon(std::string condition, bool daytime)
{
  if (condition == "clear-night") return ICON_w_clear_night;
  if (condition == "cloudy") return ICON_w_cloudy;
  if (condition == "fog") return ICON_w_fog;
  if (condition == "hail") return ICON_w_hail;
  if (condition == "lightning") return ICON_w_lightning;
  if (condition == "lightning-rainy") return ICON_w_lightning_rainy;
  if (condition == "partlycloudy" && !daytime) return ICON_w_night_partly_cloudy;
  if (condition == "partlycloudy" && daytime) return ICON_w_partly_cloudy;
  if (condition == "pouring") return ICON_w_pouring;
  if (condition == "rainy") return ICON_w_rainy;
  if (condition == "snowy") return ICON_w_snowy;
  if (condition == "snowy-rainy") return ICON_w_snowy_rainy;
  if (condition == "sunny") return ICON_w_sunny;
  if (condition == "windy") return ICON_w_windy;
  if (condition == "windy-variant") return ICON_w_windy_variant;
  if (condition == "exceptional") return ICON_w_exceptional;
  return "";
}

#define ICON_moon_first_quarter "\U000F0F61"
#define ICON_moon_full "\U000F0F62"
#define ICON_moon_last_quarter "\U000F0F63"
#define ICON_moon_new "\U000F0F64"
#define ICON_moon_waning_crescent "\U000F0F65"
#define ICON_moon_waning_gibbous "\U000F0F66"
#define ICON_moon_waxing_crescent "\U000F0F67"
#define ICON_moon_waxing_gibbous "\U000F0F68"

std::string moonToIcon(std::string moonPhase)
{
  if (moonPhase == "new_moon") return ICON_moon_new;
  if (moonPhase == "waxing_crescent") return ICON_moon_waxing_crescent;
  if (moonPhase == "first_quarter") return ICON_moon_first_quarter;
  if (moonPhase == "waxing_gibbous") return ICON_moon_waxing_gibbous;
  if (moonPhase == "full_moon") return ICON_moon_full;
  if (moonPhase == "waning_gibbous") return ICON_moon_waning_gibbous;
  if (moonPhase == "last_quarter") return ICON_moon_last_quarter;
  if (moonPhase == "waning_crescent") return ICON_moon_waning_crescent;
  return "";
}

std::string locationToHungarian(std::string location, std::string distance)
{
  if (location == "home") return "Home";
  if (location == "not_home") return "Away (" + distance + ")";
  return location;
}
