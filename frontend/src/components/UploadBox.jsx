import { useState, useRef } from 'react';
import { useLang } from '../context/LangContext';

export default function UploadBox({ onSuccess }) {
  const { t } = useLang();
  const [dragover, setDragover] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileRef = useRef(null);

  async function uploadFile(file) {
    if (!file || uploading) return;
    setUploading(true);
    setError('');
    const fd = new FormData();
    fd.append('save_file', file);
    try {
      const r = await fetch('/api/upload', { method: 'POST', body: fd });
      const d = await r.json();
      if (d.success) {
        if (onSuccess) onSuccess(d);
      } else {
        setError(d.error || t('error'));
      }
    } catch (e) {
      setError(t('net_error'));
    } finally {
      setUploading(false);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragover(false);
    if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
  }

  function handleDragOver(e) {
    e.preventDefault();
    setDragover(true);
  }

  return (
    <div className="page-center">
      <div
        className={`upload-box${dragover ? ' dragover' : ''}`}
        onClick={() => fileRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={() => setDragover(false)}
        onDrop={handleDrop}
      >
        <h2>&#128190; {t('upload_title')}</h2>
        <p dangerouslySetInnerHTML={{ __html: t('upload_hint') }} />
        {uploading && (
          <p><span className="loading-spinner" /> {t('loading')}</p>
        )}
        {error && <p className="error-msg">{error}</p>}
        <input
          ref={fileRef}
          type="file"
          accept=".sav"
          style={{ display: 'none' }}
          onChange={(e) => { if (e.target.files[0]) uploadFile(e.target.files[0]); }}
        />
      </div>

      <div
        style={{
          maxWidth: 520,
          margin: '20px auto 0',
          textAlign: 'left',
          background: '#e8dcc0',
          border: '2px solid #8a6e48',
          borderRadius: 8,
          padding: '16px 20px',
          fontSize: 13,
          color: '#5c3d2e',
          lineHeight: 1.6,
        }}
      >
        <h3 style={{ fontSize: 18, fontWeight: 700, color: '#3a2e1e', marginBottom: 8 }}>
          &#128269; {t('where_save')}
        </h3>
        <p><b>Windows:</b> {t('win_path_hint')}</p>
        <code
          style={{
            display: 'block',
            background: '#d8cca8',
            padding: '8px 12px',
            borderRadius: 4,
            margin: '6px 0',
            wordBreak: 'break-all',
            fontSize: 12,
          }}
        >
          %AppData%\Glaiel Games\Mewgenics
        </code>
        <p>
          {t('win_full_path')}{' '}
          <code style={{ fontSize: 11 }}>
            C:\Users\&lt;YourName&gt;\AppData\Roaming\Glaiel Games\Mewgenics\
          </code>
        </p>
        <p
          style={{ marginTop: 6 }}
          dangerouslySetInnerHTML={{ __html: t('win_save_hint') }}
        />
        <p style={{ marginTop: 6 }}><b>{t('steam_deck_linux')}</b></p>
        <code
          style={{
            display: 'block',
            background: '#d8cca8',
            padding: '8px 12px',
            borderRadius: 4,
            margin: '6px 0',
            wordBreak: 'break-all',
            fontSize: 12,
          }}
        >
          ~/.local/share/Glaiel Games/Mewgenics/
        </code>
        <p style={{ marginTop: 8, fontSize: 11, color: '#8a7050' }}>
          &#9888; {t('hidden_folder_hint')}
        </p>
      </div>
    </div>
  );
}
