import { createContext, useContext, useState, useCallback } from 'react';

const translations = {
  feed: { en: 'Feed', ru: 'Лента' },
  my_cats: { en: 'My Cats', ru: 'Мои коты' },
  login: { en: 'Log in', ru: 'Войти' },
  logout: { en: 'Log out', ru: 'Выйти' },
  login_prompt: { en: 'Log in to manage cats', ru: 'Войдите чтобы управлять котами' },
  login_subtitle: { en: 'Upload saves and generate unique art', ru: 'Загружайте сохранения и генерируйте уникальные арты' },
  login_google: { en: 'Log in with Google', ru: 'Войти через Google' },
  generations: { en: 'generations', ru: 'генераций' },
  upload_title: { en: 'Upload Save File', ru: 'Загрузите сохранение' },
  upload_hint: { en: 'Drag a <strong>.sav</strong> file here or click to select', ru: 'Перетащите файл <strong>.sav</strong> сюда или нажмите для выбора' },
  where_save: { en: 'Where to find save file?', ru: 'Где найти файл сохранения?' },
  search: { en: 'Search...', ru: 'Поиск...' },
  sort: { en: 'Sort:', ru: 'Сортировка:' },
  sort_img: { en: 'Art + newest', ru: 'Арт + новые' },
  sort_new: { en: 'Newest', ru: 'Новорождённые' },
  sort_old: { en: 'Oldest', ru: 'Старейшие' },
  sort_name_az: { en: 'Name A-Z', ru: 'Имя А-Я' },
  sort_name_za: { en: 'Name Z-A', ru: 'Имя Я-А' },
  sort_class: { en: 'By class', ru: 'По классу' },
  filter_class: { en: 'Class:', ru: 'Класс:' },
  filter_all: { en: 'All', ru: 'Все' },
  filter_status: { en: 'Status:', ru: 'Статус:' },
  filter_alive: { en: 'Alive', ru: 'Живые' },
  filter_injured: { en: 'Injured', ru: 'Раненые' },
  filter_dead: { en: 'Dead', ru: 'Мёртвые' },
  filter_retired: { en: 'Retired', ru: 'Ретирован' },
  filter_donated: { en: 'Donated', ru: 'Отдан' },
  filter_gender: { en: 'Gender:', ru: 'Пол:' },
  filter_male: { en: 'Male', ru: 'Кот' },
  filter_female: { en: 'Female', ru: 'Кошка' },
  filter_image: { en: 'Image:', ru: 'Арт:' },
  filter_with_art: { en: 'With art', ru: 'С артом' },
  filter_no_art: { en: 'No art', ru: 'Без арта' },
  new_save: { en: 'New save', ru: 'Новый сейв' },
  day: { en: 'Day', ru: 'День' },
  gold: { en: 'Gold', ru: 'Золото' },
  food: { en: 'Food', ru: 'Еда' },
  coins: { en: 'Coins', ru: 'Монеты' },
  collars: { en: 'Collars', ru: 'Ошейники' },
  generate: { en: 'Generate', ru: 'Генерация' },
  regenerate: { en: 'Regenerate', ru: 'Перегенерить' },
  publish: { en: 'To feed', ru: 'В ленту' },
  unpublish: { en: 'Remove', ru: 'Убрать' },
  published_toast: { en: 'Published!', ru: 'Опубликовано!' },
  unpublished_toast: { en: 'Removed from feed', ru: 'Убрано из ленты' },
  share: { en: 'Share', ru: 'Поделиться' },
  link_copied: { en: 'Link copied!', ru: 'Ссылка скопирована!' },
  login_to_like: { en: 'Log in to like', ru: 'Войдите чтобы лайкать' },
  empty_feed: { en: 'No cats published yet', ru: 'Пока никто не опубликовал котов' },
  empty_feed_hint: { en: 'Log in, upload a save and publish!', ru: 'Войдите, загрузите сохранение и опубликуйте!' },
  feedback_title: { en: 'Feedback / Bug Report', ru: 'Обратная связь / Баг-репорт' },
  fb_name: { en: 'Your name (optional)', ru: 'Ваше имя (необязательно)' },
  fb_email: { en: 'Email for reply', ru: 'Email для ответа' },
  fb_message: { en: 'Describe the bug or leave feedback...', ru: 'Опишите баг или оставьте пожелание...' },
  fb_send: { en: 'Send', ru: 'Отправить' },
  fb_cancel: { en: 'Cancel', ru: 'Отмена' },
  fb_thanks: { en: 'Thank you for your feedback!', ru: 'Спасибо за обратную связь!' },
  fb_empty: { en: 'Please write a message', ru: 'Напишите сообщение' },
  days: { en: 'd.', ru: 'дн.' },
  dead: { en: 'Dead', ru: 'Мёртв' },
  injured: { en: 'Injured', ru: 'Ранен' },
  retired_badge: { en: 'Ret.', ru: 'Рет.' },
  in_feed: { en: 'In feed', ru: 'В ленте' },
  net_error: { en: 'Network error', ru: 'Ошибка сети' },
  loading: { en: 'Loading...', ru: 'Загрузка...' },
  error: { en: 'Error', ru: 'Ошибка' },
  sending: { en: 'Sending...', ru: 'Отправка...' },
  male: { en: 'Male', ru: 'Кот' },
  female: { en: 'Female', ru: 'Кошка' },
  spider_cat: { en: 'Spider cat', ru: 'Кот-паук' },
  breed: { en: 'Breed:', ru: 'Порода:' },
  age: { en: 'Age:', ru: 'Возраст:' },
  born: { en: 'Born:', ru: 'Рождён:' },
  born_day: { en: 'day', ru: 'день' },
  inbreeding: { en: 'Inbreeding:', ru: 'Инбридинг:' },
  parents: { en: 'Parents:', ru: 'Родители:' },
  voice: { en: 'Voice:', ru: 'Голос:' },
  focus: { en: 'Focus', ru: 'Фокус' },
  attacks: { en: 'Attacks', ru: 'Атаки' },
  passives_label: { en: 'Passives', ru: 'Пассивки' },
  items_label: { en: 'Items', ru: 'Предметы' },
  mutations_label: { en: 'Mutations', ru: 'Мутации' },
  defects_label: { en: 'Defects', ru: 'Дефекты' },
  birth_defect: { en: 'Birth defect', ru: 'Врождённый дефект' },
  defect_suffix: { en: ' (defect)', ru: ' (дефект)' },
  none: { en: 'none', ru: 'нет' },
  prompt_title: { en: 'Prompt', ru: 'Промпт' },
  cancel: { en: 'Cancel', ru: 'Отмена' },
  copy_link: { en: 'Copy the link:', ru: 'Скопируйте ссылку:' },
  of: { en: 'of', ru: 'из' },
  cats_loaded: { en: 'cats!', ru: 'котов!' },
  footer_about: { en: 'Fan-made project for viewing and generating cat art from <b>Mewgenics</b> by Edmund McMillen.', ru: 'Fan-made проект для просмотра и генерации артов котов из игры <b>Mewgenics</b> от Edmund McMillen.' },
  footer_disclaimer: { en: 'Not an official Team Meat product.', ru: 'Не является официальным продуктом Team Meat.' },
  footer_author: { en: 'Author', ru: 'Автор' },
  footer_created_by: { en: 'Created by', ru: 'Создано' },
  footer_feedback: { en: 'Feedback', ru: 'Обратная связь' },
  footer_license: { en: 'License', ru: 'Лицензия' },
  footer_license_text: { en: 'All game assets and characters belong to Edmund McMillen / Team Meat.', ru: 'Все игровые ассеты и персонажи принадлежат Edmund McMillen / Team Meat.' },
  footer_license_text2: { en: 'This project is purely fan-made and non-commercial.', ru: 'Данный проект носит исключительно фанатский характер и не преследует коммерческих целей.' },
  report_bug: { en: 'Report a bug', ru: 'Сообщить о баге' },
  win_path_hint: { en: 'Open File Explorer and paste into the address bar:', ru: 'Откройте проводник и вставьте в адресную строку:' },
  win_full_path: { en: 'Full path:', ru: 'Полный путь:' },
  win_save_hint: { en: 'Inside, find the folder with your <b>Steam ID</b>, then <code>saves</code>. Files are named <b>steamcampaign01.sav</b>, <b>steamcampaign02.sav</b>, etc. — one per campaign (max 3).', ru: 'Внутри найдите папку с вашим <b>Steam ID</b>, затем <code>saves</code>. Файлы называются <b>steamcampaign01.sav</b>, <b>steamcampaign02.sav</b> и т.д. — по одному на каждый кампейн (максимум 3).' },
  hidden_folder_hint: { en: 'AppData is a hidden folder. If you don\'t see it, enable hidden files in Explorer, or just paste the %AppData% path into the address bar.', ru: 'AppData — скрытая папка. Если не видите её, включите показ скрытых файлов в проводнике, либо просто вставьте путь с %AppData% в адресную строку.' },
  waitlist_title: { en: 'You\'re on the waitlist!', ru: 'Вы в очереди!' },
  waitlist_desc: { en: 'We\'re gradually letting people in. Your position:', ru: 'Мы постепенно открываем доступ. Ваша позиция:' },
  waitlist_of: { en: 'of', ru: 'из' },
  waitlist_hint: { en: 'We\'ll notify you when access is granted. In the meantime, check out the public feed!', ru: 'Мы откроем вам доступ в ближайшее время. А пока — смотрите публичную ленту!' },
  waitlist_badge: { en: 'Waitlist', ru: 'Очередь' },
  filter_ok: { en: 'OK', ru: 'OK' },
  admin: { en: 'Admin', ru: 'Админ' },
  steam_deck_linux: { en: 'Steam Deck / Linux:', ru: 'Steam Deck / Linux:' },
};

const LangContext = createContext();

function getLangFromCookie() {
  const match = document.cookie.match(/lang=(\w+)/);
  return match ? match[1] : 'ru';
}

export function LangProvider({ children }) {
  const [lang, setLangState] = useState(getLangFromCookie);

  const t = useCallback((key) => {
    const entry = translations[key];
    if (!entry) return key;
    return entry[lang] || entry['en'] || key;
  }, [lang]);

  const setLang = useCallback(async (newLang) => {
    setLangState(newLang);
    document.cookie = `lang=${newLang};path=/;max-age=${365 * 24 * 3600};samesite=lax`;
    try {
      await fetch('/api/set-lang', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lang: newLang }),
      });
    } catch (e) { /* ignore */ }
  }, []);

  return (
    <LangContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  const ctx = useContext(LangContext);
  if (!ctx) throw new Error('useLang must be used within LangProvider');
  return ctx;
}

export default LangContext;
