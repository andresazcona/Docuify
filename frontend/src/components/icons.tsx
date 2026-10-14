import type { ReactNode } from "react";

function Icon({ children, size = 18 }: { children: ReactNode; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

/** The Folio mark: a page with a folded corner and a bookmark ribbon. */
export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="var(--accent)" />
      <path d="M9.5 6.5h9l4.5 4.5v14.5h-13.5z" fill="var(--accent-ink)" opacity=".95" />
      <path d="M18.5 6.5v4.5H23" fill="none" stroke="var(--accent)" strokeWidth="1.4" strokeLinejoin="round" />
      <path d="M12.5 15.5h7M12.5 18.5h7M12.5 21.5h4" stroke="var(--accent)" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

export const FileIcon = () => (
  <Icon>
    <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
    <path d="M14 3v5h5M9 13h6M9 17h4" />
  </Icon>
);
export const UploadIcon = () => (
  <Icon size={22}>
    <path d="M12 16V4M7 9l5-5 5 5M5 20h14" />
  </Icon>
);
export const SendIcon = () => (
  <Icon>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </Icon>
);
export const StopIcon = () => (
  <Icon>
    <rect x="6" y="6" width="12" height="12" rx="2" />
  </Icon>
);
export const CloseIcon = () => (
  <Icon>
    <path d="M6 6l12 12M18 6L6 18" />
  </Icon>
);
export const MenuIcon = () => (
  <Icon>
    <path d="M4 7h16M4 12h16M4 17h16" />
  </Icon>
);
export const SunIcon = () => (
  <Icon>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6L7 7M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4" />
  </Icon>
);
export const MoonIcon = () => (
  <Icon>
    <path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z" />
  </Icon>
);
export const QuoteIcon = () => (
  <Icon>
    <path d="M7 7h4v4c0 3-1.5 5-4 6M15 7h4v4c0 3-1.5 5-4 6" />
  </Icon>
);
export const LinkIcon = () => (
  <Icon>
    <path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1" />
  </Icon>
);
