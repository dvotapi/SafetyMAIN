import { HazardObjectPage } from "@/features/hazards";

export default async function Page({
  params,
}: {
  params: Promise<{ hazardId: string }>;
}) {
  const { hazardId } = await params;
  return <HazardObjectPage hazardId={hazardId} />;
}
