"use client";

import { Home, Image, Languages, Video } from "lucide-react";
import { usePathname } from "next/navigation";
import { SidebarMenuButton, SidebarMenuItem } from "../ui/sidebar";
import Link from "next/link";

export default function SidebarMenuItems() {
  const path = usePathname();

  let items = [
    { title: "Home", url: "/", icon: Home, active: false },
    { title: "Photo to Video", url: "/photo-to-video", icon: Image, active: false },
    { title: "Translate Video", url: "/translate-video", icon: Languages, active: false },
    { title: "Change Video Audio", url: "/change-video-audio", icon: Video, active: false },
  ];

  items = items.map((item) => ({
    ...item,
    active: path === item.url,
  }));

  return (
    <>
      {items.map((item) => (
        <SidebarMenuItem key={item.title}>
          <SidebarMenuButton asChild isActive={item.active}>
            <Link href={item.url}>
              <item.icon />
              <span>{item.title}</span>
            </Link>
          </SidebarMenuButton>
        </SidebarMenuItem>
      ))}
    </>
  );
}
