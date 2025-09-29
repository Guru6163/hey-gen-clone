import { headers } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";
import { ClientHome } from "~/components/client-home";
import { auth } from "~/lib/auth";
import { getPresignedUrl } from "~/lib/s3";
import { db } from "~/server/db";
import { formatDistanceToNow } from "date-fns/formatDistanceToNow";

export default async function Page() {




  return <ClientHome recentCreations={[]} />;
}
