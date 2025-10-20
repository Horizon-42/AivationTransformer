# Aviation Accident Events Table Analysis

This table contains detailed information about aviation accident events, with each column representing a specific attribute of the event. Below is an analysis of the information present:

## Key Information Categories

### 1. Event Identification
- **ev_id**: Unique event identifier
- **ntsb_no**: NTSB case number
- **ev_type**: Event type (e.g., ACC for accident)
- **ev_date**: Date and time of the event
- **ev_dow**: Day of week
- **ev_time**: Event time (local or UTC)
- **ev_tmzn**: Time zone

### 2. Location Details
- **ev_city**: City where event occurred
- **ev_state**: State (US) or province (Canada)
- **ev_country**: Country
- **ev_site_zipcode**: Zip code of event site
- **latitude/longitude**: Coordinates in aviation format
- **dec_latitude/dec_longitude**: Decimal coordinates
- **latlong_acq**: Acquisition method for coordinates

### 3. Airport Information
- **apt_name**: Airport name
- **ev_nr_apt_id**: Nearest airport ID
- **ev_nr_apt_loc**: Nearest airport location
- **apt_dist**: Distance to airport
- **apt_dir**: Direction to airport
- **apt_elev**: Airport elevation

### 4. Weather and Environmental Conditions
- **wx_brief_comp**: Weather briefing company
- **wx_src_iic**: Weather source
- **wx_obs_time**: Weather observation time
- **wx_obs_dir**: Wind direction at observation
- **wx_obs_fac_id**: Weather observation facility ID
- **wx_obs_elev**: Facility elevation
- **wx_obs_dist**: Distance to facility
- **wx_obs_tmzn**: Facility time zone
- **light_cond**: Lighting conditions (e.g., DAYL)
- **sky_cond_nonceil/sky_nonceil_ht**: Sky condition and height (no ceiling)
- **sky_ceil_ht/sky_cond_ceil**: Ceiling height and condition
- **vis_sm**: Visibility in statute miles
- **wx_temp/wx_dew_pt**: Temperature and dew point
- **wind_dir_deg/wind_dir_ind**: Wind direction and indicator
- **wind_vel_kts/wind_vel_ind**: Wind speed and indicator
- **gust_ind/gust_kts**: Gust indicator and speed
- **altimeter**: Altimeter setting
- **wx_dens_alt**: Density altitude
- **wx_int_precip**: Precipitation
- **metar**: METAR weather report
- **wx_cond_basic**: Basic weather condition (e.g., VMC)

### 5. Accident Type and Collision
- **mid_air**: Mid-air collision indicator
- **on_ground_collision**: On-ground collision indicator

### 6. Injury and Fatality Data
- **ev_highest_injury**: Highest injury severity
- **inj_f_grnd/inj_m_grnd/inj_s_grnd**: Fatal, minor, serious injuries on ground
- **inj_tot_f/inj_tot_m/inj_tot_n/inj_tot_s/inj_tot_t**: Total injuries (fatal, minor, none, serious, total)

### 7. Investigation and Notification
- **invest_agy**: Investigating agency
- **ntsb_docket**: NTSB docket number
- **ntsb_notf_from/ntsb_notf_date/ntsb_notf_tm**: Notification details
- **fiche_number**: Fiche number

### 8. Change Tracking
- **lchg_date**: Last change date
- **lchg_userid**: Last change user ID

### 9. Regulatory and Office Info
- **faa_dist_office**: FAA district office

## Summary

This table provides a comprehensive dataset for aviation accident analysis, including:
- Event identification and timing
- Location and airport proximity
- Weather and environmental conditions
- Accident type and collision indicators
- Injury and fatality statistics
- Investigation and notification details
- Change tracking and regulatory info

Such a dataset is suitable for statistical analysis, geospatial mapping, risk assessment, and regulatory reporting in aviation safety research.
