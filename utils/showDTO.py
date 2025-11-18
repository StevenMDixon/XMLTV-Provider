from dataclasses import dataclass

@dataclass
class ShowDTO:
    name: str
    startDate: str
    endDate: str
    description: str | None
    episodeNumber: int | None
    iconUrl: str | None
