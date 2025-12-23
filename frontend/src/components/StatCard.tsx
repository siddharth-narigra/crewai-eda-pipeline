'use client';

interface StatCardProps {
    value: string | number;
    label: string;
    variant?: 'default' | 'filled' | 'accent';
}

export default function StatCard({ value, label, variant = 'default' }: StatCardProps) {
    const baseClasses = "p-4 border-[3px] border-black";

    const variantClasses = {
        default: "bg-white text-black",
        filled: "bg-black text-white",
        accent: "bg-[#FFFF00] text-black",
    };

    return (
        <div className={`${baseClasses} ${variantClasses[variant]}`}>
            <div className="text-stat">{value}</div>
            <div className="text-label mt-2">{label}</div>
        </div>
    );
}
