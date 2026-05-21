#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  4 15:42:04 2026

@author: bruno
"""

# main_daily.py

import os
from generate_factors_daily import generate_factors_daily
from generate_climate_data_daily import generate_climate_data_daily


def main():
    # -------------------------
    # Variáveis equivalentes
    # -------------------------
    params = [0.0] * 44
    nfips = 0

    # Strings (equivalente character*180)
    anim_file = ""
    farm_file = ""
    param_file = ""
    temp_file = ""
    wind_file = ""
    precip_file = ""

    anim_type = ""
    country = ""
    cyear = ""
    scc = ""

    # -------------------------
    # getenv → os.getenv
    # -------------------------
    anim_type = os.getenv("ANIMAL_TYPE", "")
    cyear = os.getenv("YEAR", "")
    country = os.getenv("COUNTRY", "")
    scc = os.getenv("SCC", "")

    # ⚠️ no Fortran tá escrito TEPERATURE (erro de digitação!)
    temp_file = os.getenv("TEPERATURE", "")
    wind_file = os.getenv("WIND_SPEED", "")
    precip_file = os.getenv("PRECIPITATION", "")

    farm_file = os.getenv("FARM_CONFIG", "")
    param_file = os.getenv("PARAMETERS", "")
    anim_file = os.getenv("ANIMAL_COUNTS", "")

    # -------------------------
    # Chamadas de subroutine
    # -------------------------
    generate_climate_data_daily(
        anim_file,
        nfips,
        temp_file,
        wind_file,
        precip_file,
        cyear
    )

    print("Completed: Processing climate data==================")

    generate_factors_daily(
        nfips,
        farm_file,
        param_file,
        anim_type,
        country,
        cyear,
        scc
    )


if __name__ == "__main__":
    main()