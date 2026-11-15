import os
from pathlib import Path
from sqlalchemy.orm import Session

from server.database.config import settings
from server.repositories.user_repository import UserRepository
from server.repositories.language_repository import LanguageRepository
from server.repositories.dictionary_repository import DictionaryRepository
from server.repositories.word_repository import WordRepository
from server.services.auth_service import hash_password


def parse_data_file(filepath: Path) -> dict:
    lang_info = {}
    features = []
    dictionaries = []
    current_dict = None

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("@lang "):
                parts = [p.strip() for p in line[6:].split("|")]
                if len(parts) >= 5:
                    lang_info = {
                        "code": parts[0],
                        "name": parts[1],
                        "native": parts[2],
                        "flag": parts[3],
                        "niche": int(parts[4]),
                    }
            elif line.startswith("@feature "):
                parts = [p.strip() for p in line[9:].split("|")]
                if len(parts) >= 2:
                    features.append({"title": parts[0], "body": parts[1]})
            elif line.startswith("@dict "):
                parts = [p.strip() for p in line[6:].split("|")]
                if len(parts) >= 3:
                    current_dict = {
                        "goal": parts[0],
                        "title": parts[1],
                        "descr": parts[2],
                        "words": [],
                    }
                    dictionaries.append(current_dict)
            else:
                if current_dict is not None and "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 2:
                        word = parts[0]
                        translation = parts[1]
                        transcription = parts[2] if len(parts) > 2 else ""
                        example = parts[3] if len(parts) > 3 else ""
                        current_dict["words"].append(
                            {
                                "word": word,
                                "translation": translation,
                                "transcription": transcription,
                                "example": example,
                            }
                        )

    return {
        "lang": lang_info,
        "features": features,
        "dictionaries": dictionaries,
    }


def seed_database(db: Session) -> tuple[int, int]:
    """Заполняет базу начальными данными (языки, словари, слова, админ)."""
    user_repo = UserRepository(db)
    lang_repo = LanguageRepository(db)
    dict_repo = DictionaryRepository(db)
    word_repo = WordRepository(db)

    # 1. Администратор по умолчанию
    admin = user_repo.get_by_email(settings.ADMIN_EMAIL)
    if not admin:
        admin = user_repo.create(
            email=settings.ADMIN_EMAIL,
            username=settings.ADMIN_USERNAME,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
        )
        db.commit()

    # 2. Парсинг файлов данных
    data_dir = Path(__file__).resolve().parent.parent / "data"
    new_dicts_cnt = 0
    new_words_cnt = 0

    if data_dir.exists():
        for txt_file in sorted(data_dir.glob("*.txt")):
            parsed = parse_data_file(txt_file)
            lang_data = parsed.get("lang")
            if not lang_data:
                continue

            lang_code = lang_data["code"]
            lang = lang_repo.get_by_code(lang_code)
            if not lang:
                lang = lang_repo.create_language(
                    code=lang_code,
                    name=lang_data["name"],
                    native=lang_data["native"],
                    niche=lang_data["niche"],
                    flag=lang_data["flag"],
                )
                db.flush()

            # Фичи языка
            existing_feats = {f.title for f in lang_repo.list_features(lang_code)}
            for feat in parsed.get("features", []):
                if feat["title"] not in existing_feats:
                    lang_repo.create_feature(lang_code, feat["title"], feat["body"])
                    db.flush()

            # Словари и слова
            for d_data in parsed.get("dictionaries", []):
                # Проверяем, есть ли уже словарь с таким названием для данного языка
                existing_dicts = dict_repo.list_all(lang=lang_code, goal=d_data["goal"])
                matched_d = next((d for d in existing_dicts if d.title == d_data["title"]), None)

                if not matched_d:
                    matched_d = dict_repo.create(
                        lang=lang_code,
                        goal=d_data["goal"],
                        title=d_data["title"],
                        description=d_data["descr"],
                        author_id=admin.id,
                        is_public=True,
                    )
                    new_dicts_cnt += 1
                    db.flush()

                # Слова словаря
                existing_words = {
                    w.word.lower() for w in word_repo.list_by_dictionary(matched_d.id, limit=500)
                }
                for w_data in d_data.get("words", []):
                    if w_data["word"].lower() not in existing_words:
                        word_repo.create(
                            dict_id=matched_d.id,
                            word=w_data["word"],
                            translation=w_data["translation"],
                            transcription=w_data["transcription"],
                            example=w_data["example"],
                        )
                        new_words_cnt += 1
                        db.flush()

    db.commit()
    return new_dicts_cnt, new_words_cnt
