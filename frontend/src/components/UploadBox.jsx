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
      <div className="lab-upload">
        <div
          className={`lab-upload-zone${dragover ? ' dragover' : ''}`}
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

        <div className="lab-upload-hint">
          <h3>&#128269; {t('where_save')}</h3>
          <p><b>Windows:</b> {t('win_path_hint')}</p>
          <code style={{ display: 'block', margin: '6px 0', padding: '8px 12px', wordBreak: 'break-all', border: '1px solid #a8a49c' }}>
            %AppData%\Glaiel Games\Mewgenics
          </code>
          <p>
            {t('win_full_path')}{' '}
            <code>
              C:\Users\&lt;YourName&gt;\AppData\Roaming\Glaiel Games\Mewgenics\
            </code>
          </p>
          <p
            style={{ marginTop: 6 }}
            dangerouslySetInnerHTML={{ __html: t('win_save_hint') }}
          />
          <p style={{ marginTop: 6 }}><b>{t('steam_deck_linux')}</b></p>
          <code style={{ display: 'block', margin: '6px 0', padding: '8px 12px', wordBreak: 'break-all', border: '1px solid #a8a49c' }}>
            ~/.local/share/Glaiel Games/Mewgenics/
          </code>
          <p style={{ marginTop: 8, fontSize: 11, color: '#7a756c' }}>
            &#9888; {t('hidden_folder_hint')}
          </p>
        </div>
      </div>
    </div>
  );
}
