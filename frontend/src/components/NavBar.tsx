"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "🏠 首页" },
  { href: "/diary", label: "📔 日记" },
  { href: "/mood", label: "💝 心情" },
  { href: "/kb", label: "📚 知识库" },
];

export default function NavBar() {
  const pathname = usePathname();

  return (
    <nav className="bg-white border-b-4 border-gray-100 sticky top-0 z-10">
      <div className="max-w-4xl mx-auto flex gap-1 px-4 py-2 overflow-x-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                px-6 py-3 text-elder-base font-bold rounded-xl transition-all whitespace-nowrap
                ${isActive
                  ? "bg-elder-primary text-white shadow-md"
                  : "text-gray-600 hover:bg-gray-100 hover:text-elder-primary"
                }
              `}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
