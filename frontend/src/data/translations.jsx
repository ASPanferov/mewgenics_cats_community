import { createContext, useContext, useState, useCallback, useMemo } from 'react';

const translations = {
  ru: {
    feed: 'Лента',
    my_cats: 'Мои коты',
    login: 'Войти',
    logout: 'Выйти',
    login_prompt: 'Войдите чтобы управлять котами',
    login_subtitle: 'Загружайте сохранения и генерируйте уникальные арты',
    login_google: 'Войти через Google',
    generations: 'генераций',
    upload_title: 'Загрузите сохранение',
    upload_hint: 'Перетащите файл .sav сюда или нажмите для выбора',
    where_save: 'Где найти файл сохранения?',
    search: 'Поиск...',
    sort: 'Сортировка:',
    sort_img: 'Арт + новые',
    sort_new: 'Новорождённые',
    sort_old: 'Старейшие',
    sort_name_az: 'Имя А-Я',
    sort_name_za: 'Имя Я-А',
    sort_class: 'По классу',
    filter_class: 'Класс:',
    filter_all: 'Все',
    filter_status: 'Статус:',
    filter_alive: 'Живые',
    filter_injured: 'Раненые',
    filter_dead: 'Мёртвые',
    filter_retired: 'Ретирован',
    filter_donated: 'Отдан',
    filter_gender: 'Пол:',
    filter_male: 'Кот',
    filter_female: 'Кошка',
    filter_image: 'Арт:',
    filter_with_art: 'С артом',
    filter_no_art: 'Без арта',
    new_save: 'Новый сейв',
    day: 'День',
    gold: 'Золото',
    generate: 'Генерация',
    regenerate: 'Перегенерить',
    publish: 'В ленту',
    unpublish: 'Убрать',
    published_toast: 'Опубликовано!',
    unpublished_toast: 'Убрано из ленты',
    share: 'Поделиться',
    link_copied: 'Ссылка скопирована!',
    login_to_like: 'Войдите чтобы лайкать',
    empty_feed: 'Пока никто не опубликовал котов',
    empty_feed_hint: 'Войдите, загрузите сохранение и опубликуйте!',
    feedback_title: 'Обратная связь / Баг-репорт',
    fb_name: 'Ваше имя (необязательно)',
    fb_email: 'Email для ответа',
    fb_message: 'Опишите баг или оставьте пожелание...',
    fb_send: 'Отправить',
    fb_cancel: 'Отмена',
    fb_thanks: 'Спасибо за обратную связь!',
    fb_empty: 'Напишите сообщение',
    days: 'дн.',
    dead: 'Мёртв',
    injured: 'Ранен',
    retired_badge: 'Рет.',
    in_feed: 'В ленте',
    net_error: 'Ошибка сети',
    loading: 'Загрузка...',
    error: 'Ошибка',
    sending: 'Отправка...',
    male: 'Кот',
    female: 'Кошка',
    spider_cat: 'Кот-паук',
    breed: 'Порода:',
    age: 'Возраст:',
    born: 'Рождён:',
    born_day: 'день',
    inbreeding: 'Инбридинг:',
    parents: 'Родители:',
    voice: 'Голос:',
    focus: 'Фокус',
    attacks: 'Атаки',
    passives_label: 'Пассивки',
    items_label: 'Предметы',
    mutations_label: 'Мутации',
    defects_label: 'Дефекты',
    birth_defect: 'Врождённый дефект',
    defect_suffix: ' (дефект)',
    none: 'нет',
    prompt_title: 'Промпт',
    cancel: 'Отмена',
    copy_link: 'Скопируйте ссылку:',
    of: 'из',
    food: 'Еда',
    coins: 'Монеты',
    collars: 'Ошейники',
    cats_loaded: 'котов!',
    footer_about: 'Fan-made проект для просмотра и генерации артов котов из игры Mewgenics от Edmund McMillen.',
    footer_disclaimer: 'Не является официальным продуктом Team Meat.',
    footer_author: 'Автор',
    footer_created_by: 'Создано',
    footer_feedback: 'Обратная связь',
    footer_license: 'Лицензия',
    footer_license_text: 'Все игровые ассеты и персонажи принадлежат Edmund McMillen / Team Meat.',
    footer_license_text2: 'Данный проект носит исключительно фанатский характер и не преследует коммерческих целей.',
    report_bug: 'Сообщить о баге',
    win_path_hint: 'Откройте проводник и вставьте в адресную строку:',
    win_full_path: 'Полный путь:',
    win_save_hint: 'Внутри найдите папку с вашим Steam ID, затем saves. Файлы называются steamcampaign01.sav и т.д.',
    hidden_folder_hint: 'AppData — скрытая папка. Если не видите её, включите показ скрытых файлов.',
    waitlist_title: 'Вы в очереди!',
    waitlist_desc: 'Мы постепенно открываем доступ. Ваша позиция:',
    waitlist_of: 'из',
    waitlist_hint: 'Мы откроем вам доступ в ближайшее время. А пока — смотрите публичную ленту!',
    waitlist_badge: 'Очередь',
  },
  en: {
    feed: 'Feed',
    my_cats: 'My Cats',
    login: 'Log in',
    logout: 'Log out',
    login_prompt: 'Log in to manage cats',
    login_subtitle: 'Upload saves and generate unique art',
    login_google: 'Log in with Google',
    generations: 'generations',
    upload_title: 'Upload Save File',
    upload_hint: 'Drag a .sav file here or click to select',
    where_save: 'Where to find save file?',
    search: 'Search...',
    sort: 'Sort:',
    sort_img: 'Art + newest',
    sort_new: 'Newest',
    sort_old: 'Oldest',
    sort_name_az: 'Name A-Z',
    sort_name_za: 'Name Z-A',
    sort_class: 'By class',
    filter_class: 'Class:',
    filter_all: 'All',
    filter_status: 'Status:',
    filter_alive: 'Alive',
    filter_injured: 'Injured',
    filter_dead: 'Dead',
    filter_retired: 'Retired',
    filter_donated: 'Donated',
    filter_gender: 'Gender:',
    filter_male: 'Male',
    filter_female: 'Female',
    filter_image: 'Image:',
    filter_with_art: 'With art',
    filter_no_art: 'No art',
    new_save: 'New save',
    day: 'Day',
    gold: 'Gold',
    generate: 'Generate',
    regenerate: 'Regenerate',
    publish: 'To feed',
    unpublish: 'Remove',
    published_toast: 'Published!',
    unpublished_toast: 'Removed from feed',
    share: 'Share',
    link_copied: 'Link copied!',
    login_to_like: 'Log in to like',
    empty_feed: 'No cats published yet',
    empty_feed_hint: 'Log in, upload a save and publish!',
    feedback_title: 'Feedback / Bug Report',
    fb_name: 'Your name (optional)',
    fb_email: 'Email for reply',
    fb_message: 'Describe the bug or leave feedback...',
    fb_send: 'Send',
    fb_cancel: 'Cancel',
    fb_thanks: 'Thank you for your feedback!',
    fb_empty: 'Please write a message',
    days: 'd.',
    dead: 'Dead',
    injured: 'Injured',
    retired_badge: 'Ret.',
    in_feed: 'In feed',
    net_error: 'Network error',
    loading: 'Loading...',
    error: 'Error',
    sending: 'Sending...',
    male: 'Male',
    female: 'Female',
    spider_cat: 'Spider cat',
    breed: 'Breed:',
    age: 'Age:',
    born: 'Born:',
    born_day: 'day',
    inbreeding: 'Inbreeding:',
    parents: 'Parents:',
    voice: 'Voice:',
    focus: 'Focus',
    attacks: 'Attacks',
    passives_label: 'Passives',
    items_label: 'Items',
    mutations_label: 'Mutations',
    defects_label: 'Defects',
    birth_defect: 'Birth defect',
    defect_suffix: ' (defect)',
    none: 'none',
    prompt_title: 'Prompt',
    cancel: 'Cancel',
    copy_link: 'Copy the link:',
    of: 'of',
    food: 'Food',
    coins: 'Coins',
    collars: 'Collars',
    cats_loaded: 'cats!',
    footer_about: 'Fan-made project for viewing and generating cat art from Mewgenics by Edmund McMillen.',
    footer_disclaimer: 'Not an official Team Meat product.',
    footer_author: 'Author',
    footer_created_by: 'Created by',
    footer_feedback: 'Feedback',
    footer_license: 'License',
    footer_license_text: 'All game assets and characters belong to Edmund McMillen / Team Meat.',
    footer_license_text2: 'This project is purely fan-made and non-commercial.',
    report_bug: 'Report a bug',
    win_path_hint: 'Open File Explorer and paste into the address bar:',
    win_full_path: 'Full path:',
    win_save_hint: 'Inside, find the folder with your Steam ID, then saves. Files are named steamcampaign01.sav, etc.',
    hidden_folder_hint: 'AppData is a hidden folder. Enable hidden files in Explorer, or paste the %AppData% path.',
    waitlist_title: "You're on the waitlist!",
    waitlist_desc: "We're gradually letting people in. Your position:",
    waitlist_of: 'of',
    waitlist_hint: "We'll notify you when access is granted. In the meantime, check out the public feed!",
    waitlist_badge: 'Waitlist',
  },
};

export default translations;

/* ---- Language Context & Hook ---- */

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[1]) : null;
}

function setCookie(name, value, days = 365) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)};expires=${expires};path=/;SameSite=Lax`;
}

const LangContext = createContext(null);

export function LangProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    const saved = getCookie('lang');
    if (saved && translations[saved]) return saved;
    const browserLang = navigator.language?.slice(0, 2);
    return browserLang === 'ru' ? 'ru' : 'en';
  });

  const setLang = useCallback((newLang) => {
    if (translations[newLang]) {
      setLangState(newLang);
      setCookie('lang', newLang);
    }
  }, []);

  const t = useCallback((key) => {
    return translations[lang]?.[key] ?? translations.en?.[key] ?? key;
  }, [lang]);

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t]);

  return (
    <LangContext.Provider value={value}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  const ctx = useContext(LangContext);
  if (!ctx) throw new Error('useLang must be used within a LangProvider');
  return ctx;
}
