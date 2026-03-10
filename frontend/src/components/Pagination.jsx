import React, { useMemo } from 'react';

const baseBtn = {
  padding: '6px 12px',
  background: '#e8d5a8',
  color: '#3a2518',
  border: '2px solid #8b6914',
  borderRadius: '4px',
  cursor: 'pointer',
  fontFamily: "'EdmundMcMillen', 'Peralta', serif",
  fontSize: '13px',
  minWidth: '36px',
  transition: 'all 0.15s',
};

const styles = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '6px',
    flexWrap: 'wrap',
    padding: '12px 0',
    fontFamily: "'EdmundMcMillen', 'Peralta', serif",
  },
  btn: baseBtn,
  btnActive: {
    ...baseBtn,
    background: '#3a2518',
    color: '#d4a843',
    border: '2px solid #d4a843',
    fontWeight: 'bold',
    cursor: 'default',
  },
  btnDisabled: {
    ...baseBtn,
    opacity: 0.4,
    cursor: 'not-allowed',
  },
  ellipsis: {
    padding: '6px 4px',
    color: '#6b4c2a',
    fontSize: '13px',
    userSelect: 'none',
  },
  info: {
    color: '#6b4c2a',
    fontSize: '12px',
    marginLeft: '12px',
  },
};

function getPageNumbers(current, total, maxVisible = 7) {
  if (total <= maxVisible) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  const pages = [];
  const half = Math.floor((maxVisible - 2) / 2);
  let start = Math.max(2, current - half);
  let end = Math.min(total - 1, current + half);

  if (current - half < 2) {
    end = Math.min(total - 1, maxVisible - 1);
  }
  if (current + half > total - 1) {
    start = Math.max(2, total - maxVisible + 2);
  }

  pages.push(1);
  if (start > 2) pages.push('...');
  for (let i = start; i <= end; i++) pages.push(i);
  if (end < total - 1) pages.push('...');
  if (total > 1) pages.push(total);

  return pages;
}

export default function Pagination({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
}) {
  const pages = useMemo(
    () => getPageNumbers(currentPage, totalPages),
    [currentPage, totalPages]
  );

  if (totalPages <= 1) return null;

  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  const renderBtn = (label, page, disabled) => (
    <button
      key={`nav-${label}`}
      style={disabled ? styles.btnDisabled : styles.btn}
      onClick={() => !disabled && onPageChange(page)}
      disabled={disabled}
    >
      {label}
    </button>
  );

  return (
    <div style={styles.container}>
      {renderBtn('<<', 1, currentPage === 1)}
      {renderBtn('<', currentPage - 1, currentPage === 1)}

      {pages.map((page, idx) => {
        if (page === '...') {
          return <span key={`ellipsis-${idx}`} style={styles.ellipsis}>...</span>;
        }
        return (
          <button
            key={page}
            style={page === currentPage ? styles.btnActive : styles.btn}
            onClick={() => page !== currentPage && onPageChange(page)}
          >
            {page}
          </button>
        );
      })}

      {renderBtn('>', currentPage + 1, currentPage === totalPages)}
      {renderBtn('>>', totalPages, currentPage === totalPages)}

      {totalItems != null && (
        <span style={styles.info}>
          {startItem}-{endItem} of {totalItems}
        </span>
      )}
    </div>
  );
}
