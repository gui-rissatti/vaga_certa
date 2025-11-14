import type { ParsedCv, ExperienceEntry, EducationEntry } from '../types';

export const parseCvText = (text: string): ParsedCv => {
    const lines = text.split('\n').filter(line => line.trim() !== '');
    
    const parsed: ParsedCv = {
        name: '',
        contact: {},
        summary: '',
        experience: [],
        education: [],
        skills: []
    };

    let currentSection: 'summary' | 'experience' | 'education' | 'skills' | 'contact' | null = null;

    if (lines[0]?.startsWith('# ')) {
        parsed.name = lines[0].substring(2).trim();
    }
    
    const contactLine = lines[1] || '';
    const contactParts = contactLine.split('|').map(p => p.trim());
    parsed.contact = {
        address: contactParts[0],
        phone: contactParts[1],
        email: contactParts[2],
        linkedin: contactParts[3]
    };
    
    for (let i = 2; i < lines.length; i++) {
        const line = lines[i];

        if (line.startsWith('## Summary')) {
            currentSection = 'summary';
            continue;
        } else if (line.startsWith('## Experience')) {
            currentSection = 'experience';
            continue;
        } else if (line.startsWith('## Education')) {
            currentSection = 'education';
            continue;
        } else if (line.startsWith('## Skills')) {
            currentSection = 'skills';
            continue;
        }

        switch (currentSection) {
            case 'summary':
                parsed.summary += line + '\n';
                break;
            case 'experience':
                if (line.startsWith('**')) {
                    const [roleAndCompany, location] = line.split('|').map(s => s.trim());
                    const cleanRoleCompany = roleAndCompany.replace(/\*\*/g, '').trim();
                    
                    let role = '';
                    let company = '';
                    
                    // Tenta diferentes separadores: ' na ', ' at ', ' em '
                    if (cleanRoleCompany.includes(' na ')) {
                        [role, company] = cleanRoleCompany.split(' na ').map(s => s.trim());
                    } else if (cleanRoleCompany.includes(' at ')) {
                        [role, company] = cleanRoleCompany.split(' at ').map(s => s.trim());
                    } else if (cleanRoleCompany.includes(' em ')) {
                        [role, company] = cleanRoleCompany.split(' em ').map(s => s.trim());
                    } else {
                        // Fallback: assume que é apenas o role
                        role = cleanRoleCompany;
                        company = '';
                    }
                    
                    let period = lines[++i]?.replace(/\*/g, '').trim() || '';
                    // Filtrar notas automáticas do período
                    if (period.toLowerCase().includes('(nota:') || period.toLowerCase().includes('conforme cv original')) {
                        // Remover a nota do período
                        period = period.replace(/\(Nota:.*?\)/gi, '').trim();
                    }
                    
                    const newEntry: ExperienceEntry = { role, company, period, responsibilities: [] };
                    parsed.experience.push(newEntry);
                } else if (line.startsWith('- ') && parsed.experience.length > 0) {
                    const responsibility = line.substring(2).trim();
                    // Filtrar notas automáticas indesejadas
                    if (!responsibility.toLowerCase().includes('(nota:') && 
                        !responsibility.toLowerCase().includes('conforme cv original')) {
                        parsed.experience[parsed.experience.length - 1].responsibilities.push(responsibility);
                    }
                }
                break;
            case 'education':
                 if (line.startsWith('**')) {
                    const [degreeAndInstitution, location] = line.split('|').map(s => s.trim());
                    const cleanDegreeInst = degreeAndInstitution.replace(/\*\*/g, '').trim();
                    
                    let degree = '';
                    let institution = '';
                    
                    // Tenta diferentes separadores: ' na ', ' at ', ' em '
                    if (cleanDegreeInst.includes(' na ')) {
                        [degree, institution] = cleanDegreeInst.split(' na ').map(s => s.trim());
                    } else if (cleanDegreeInst.includes(' at ')) {
                        [degree, institution] = cleanDegreeInst.split(' at ').map(s => s.trim());
                    } else if (cleanDegreeInst.includes(' em ')) {
                        [degree, institution] = cleanDegreeInst.split(' em ').map(s => s.trim());
                    } else if (cleanDegreeInst.includes(' no ')) {
                        [degree, institution] = cleanDegreeInst.split(' no ').map(s => s.trim());
                    } else {
                        degree = cleanDegreeInst;
                        institution = '';
                    }
                    
                    const period = lines[++i]?.replace(/\*/g, '').trim() || '';
                    const newEntry: EducationEntry = { degree, institution, period };
                    parsed.education.push(newEntry);
                }
                break;
            case 'skills':
                if (line.startsWith('- ')) {
                    parsed.skills = line.substring(2).split(',').map(s => s.trim());
                }
                break;
        }
    }
    
    parsed.summary = parsed.summary.trim();

    return parsed;
};
