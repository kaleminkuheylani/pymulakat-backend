-- 2026-07-19: Achievements / user_achievements tablosu
-- Her achievement unlock'u bir satir olarak kaydedilir.
-- Puanlar user_achievements.points'te tutulur, dashboard'da toplam gosterilir.

CREATE TABLE IF NOT EXISTS user_achievements (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    achievement_id VARCHAR(64) NOT NULL,
    unlocked_at TIMESTAMPTZ DEFAULT now(),
    points INT NOT NULL DEFAULT 0,
    UNIQUE (user_id, achievement_id)
);

CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id
    ON user_achievements(user_id);

CREATE INDEX IF NOT EXISTS idx_user_achievements_achievement_id
    ON user_achievements(achievement_id);
