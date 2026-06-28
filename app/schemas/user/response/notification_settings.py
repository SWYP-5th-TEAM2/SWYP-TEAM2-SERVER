from app.schemas.common import CamelModel


class NotificationSettingsResponse(CamelModel):
    candidate_place_enabled: bool
    vote_deadline_enabled: bool
    schedule_confirmed_enabled: bool
    quiet_recommendation_enabled: bool
