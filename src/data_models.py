from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SuspectMetadata(BaseModel):
    age: int = Field(..., ge=0, le=120, description="Age of the suspect")
    sex: Literal["M", "F", "U"] = Field(..., description="Sex of the suspect")
    height: float = Field(..., gt=0, le=3.0, description="Height of the suspect in meters")
    weight: float = Field(..., gt=0, le=500, description="Weight of the suspect in kilograms")
    lifetime_sports_activity: int = Field(..., ge=0,
        description="Total number of months that the suspect has been involved in sports activities within his lifetime"
    )
    target_speed: int = Field(..., gt=0, le=50,
        description="Target pace for the experiment in kilometers per hour"
    )
    watch_type: str = Field(..., min_length=1,
        description="Type of watch used for the experiment (e.g., Samsung Galaxy Watch 7)"
    )


class RunMetadata(BaseModel):
    atm_pressure: Optional[float] = Field(None, gt=0, description="Atmospheric pressure in hPa")
    temperature: Optional[float] = Field(None, gt=-273.15, description="Temperature in Celsius")
    sleep_duration: Optional[int] = Field(None, ge=0, description="Total sleep duration in minutes")
    daily_activity: Optional[float] = Field(None, ge=0, le=1440,
        description="Minutes of daily activity outside running (e.g. cycling, gym, walking)"
    )
    steps_count: Optional[float] = Field(None, ge=0, description="Total step count for the day")


class RunSecondData(BaseModel):
    timestamp: datetime = Field(..., description="Timestamp for the data point")
    heart_rate: int = Field(..., ge=20, le=300, description="Heart rate in beats per minute")


class SuspectRun(BaseModel):
    run_id: str = Field(..., min_length=1, description="Unique identifier for the run")
    metadata: RunMetadata
    per_second_data: list[RunSecondData]


class SuspectExperiment(BaseModel):
    suspect_id: str = Field(..., min_length=1)
    metadata: SuspectMetadata
    runs: list[SuspectRun]