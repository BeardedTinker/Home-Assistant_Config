#include <string>
#include <iostream>
#include <sstream>

// Conditions
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

// Moon
#define ICON_moon_first_quarter "\U000F0F61"
#define ICON_moon_full "\U000F0F62"
#define ICON_moon_last_quarter "\U000F0F63"
#define ICON_moon_new "\U000F0F64"
#define ICON_moon_waning_crescent "\U000F0F65"
#define ICON_moon_waning_gibbous "\U000F0F66"
#define ICON_moon_waxing_crescent "\U000F0F67"
#define ICON_moon_waxing_gibbous "\U000F0F68"

// Battery
#define ICON_bat_empty	"\U000F008E"
#define ICON_bat_10	"\U000F007A"
#define ICON_bat_20	"\U000F007B"
#define ICON_bat_30	"\U000F007C"
#define ICON_bat_40	"\U000F007D"
#define ICON_bat_50	"\U000F007E"
#define ICON_bat_60	"\U000F007F"
#define ICON_bat_70	"\U000F0080"
#define ICON_bat_80	"\U000F0081"
#define ICON_bat_90	"\U000F0082"
#define ICON_bat_100	"\U000F0079"

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

std::string batteryToIcon(float battery)
{
  if (battery > 90) return ICON_bat_100;
  if (battery > 80) return ICON_bat_90;
  if (battery > 70) return ICON_bat_80;
  if (battery > 60) return ICON_bat_70;
  if (battery > 50) return ICON_bat_60;
  if (battery > 40) return ICON_bat_50;
  if (battery > 30) return ICON_bat_40;
  if (battery > 20) return ICON_bat_30;
  if (battery > 10) return ICON_bat_20;
  if (battery > 0) return ICON_bat_10;
  return ICON_bat_empty;
}

std::vector<std::string> splitStringIntoVector(std::string sentence, int lineLength)
{
  // This is not the most efficient way of splitting strings, but will do the job for now!
  std::string s = sentence;
  std::vector<std::string> result;

  std::replace( s.begin(), s.end(), ',', ' ');

  std::istringstream iss(s);
  std::string line;

  do {
    std::string word;
    iss >> word;
    if (line.length() + word.length() > lineLength) {
      result.push_back(line);
      line.clear();
    }
    line += word + ",";

  }while (iss);

  if (!line.empty()) {
    result.push_back(line);
  }

  return result;
}
