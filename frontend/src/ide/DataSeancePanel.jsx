import React, { useState } from 'react';
import { X, ShieldCheck, Info } from 'lucide-react';
import { ProblemsPanel } from './ProblemsPanel';

export function DataSeancePanel({ onClose, selectedFile, fileContents }) {
  const [showCitationsModal, setShowCitationsModal] = useState(false);

  // Citations data
  const citations = [
    {
      title: "Human-Centered Artificial Intelligence: Reliable, Safe & Trustworthy",
      description: "HCAI are more likely to produce designs that are Reliable, Safe & Trustworthy (RST).Achieving these goals will dramatically increase human performance, while supporting humanself-efficacy, mastery, creativity, and responsibility",
      author: "Ben Shneiderman",
      url: "https://arxiv.org/pdf/2002.04087"
    },
    {
      title: "A BRIEF HISTORY OF AI: HOW TO PREVENT ANOTHER WINTER",
      description: "Provide a brief rundown of AI’s evolution over the course of decades, highlighting its crucial moments and major turning points from inception to the present. Indoing so, we attempt to learn, anticipate the future, and discuss what steps may be taken to preventanother ‘winter’.",
      author: "Amirhosein Toosi, Andrea Bottino, Babak Saboury, Eliot Siegel, Arman Rahmim",
      url: "https://arxiv.org/pdf/2109.01517"
    },
    {
      title: "Fairness and Abstraction in Sociotechnical Systems",
      description: " This paper draws on studies of sociotechnical systems in Science and Technology Studies to explain why such trapsoccur and how to avoid them. Finally, suggests ways in which technical designers can mitigate the traps through a refocusing of design in terms of process rather than solutions, and by drawing abstraction boundaries to include social actors rather than purely technical ones.",
      author: "Andrew D. Selbst, danah boyd, Sorelle A. Friedler, Suresh Venkatasubramanian, Janet Vertesi",
      url: "https://dl.acm.org/doi/pdf/10.1145/3287560.3287598"
    },
    {
      title: "The Malicious Use of Artificial Intelligence: Forecasting, Prevention, and Mitigation",
      description: "AI will increasingly enable sophisticated malicious attacks across digital, physical, and political domains as capabilities advance, requiring urgent development of AI-based defenses, policy frameworks, formal verification systems, and collective preparedness efforts to balance openness with security before highly capable AI systems with dangerous potential become realizable.",
      author: "Miles Brundage, Shahar Avin, Jack Clark, Helen Toner, Peter Eckersley, Ben Garfinkel, Allan Dafoe, Paul Scharre, Thomas Zeitzoff, Bobby Filar, Hyrum Anderson, Heather Roff, Gregory C. Allen, Jacob Steinhardt, Carrick Flynn, Seán Ó hÉigeartaigh, Simon Beard, Haydn Belfield, Sebastian Farquhar, Clare Lyle, Rebecca Crootof, Owain Evans, Michael Page, Joanna Bryson, Roman Yampolskiy, Dario Amodei",
      url: "https://arxiv.org/pdf/1802.07228"
    },
    {
      title: "Inclusive and Secure Artificial Intelligence: A Global Perspective on Policy and Technical Developments",
      description: "Culture is central to AI equity and trust, as systems reflecting implicit cultural assumptions can perpetuate discrimination when ignoring diversity, but culturally informed design that incorporates regional values, linguistic diversity, and local knowledge through cross-border collaboration between developers, policymakers, and communities—supported by cultural institutions investing in education and partnerships—can create inclusive, contextually grounded AI systems that enhance effectiveness, fairness, and ethical outcomes across global societies.",
      author: "Saiph Savage, Lili Savage",
      url: "https://opus.bsz-bw.de/ifa/frontdoor/deliver/index/docId/1570/file/ifa-2025_savage_inclusive-secure-AI.pdf"
    },
    {
      title: "AI Ethics Guidelines - UNESCO",
      description: "Recommendation on the Ethics of Artificial Intelligence",
      url: "https://www.unesco.org/en/artificial-intelligence/recommendation-ethics"
    },
    {
      title: "CCPA - California Consumer Privacy Act",
      description: "California law protecting consumer privacy rights",
      url: "https://oag.ca.gov/privacy/ccpa"
    },
    {
      title: "Algorithmic Accountability Act",
      description: "U.S. legislation for impact assessments of automated decision systems",
      url: "https://www.congress.gov/bill/117th-congress/house-bill/6580"
    }
  ];

  const containerStyle = {
    width: '384px',
    backgroundColor: '#252526',
    borderLeft: '1px solid #3e3e42',
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
  };

  const headerStyle = {
    height: '36px', 
    backgroundColor: '#2d2d30',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingLeft: '12px',
    paddingRight: '12px',
    borderBottom: '1px solid #3e3e42',
  };

  const headerLeftStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  };

  const titleStyle = {
    fontSize: '14px',
    color: '#cccccc',
  };

  const iconButtonStyle = {
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '4px',
    padding: '4px',
    cursor: 'pointer',
    color: '#cccccc',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 0.2s ease',
  };

  const closeButtonStyle = {
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '4px',
    padding: '4px',
    cursor: 'pointer',
    color: '#cccccc',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 0.2s ease',
  };

  const contentStyle = {
    flex: 1,
    overflow: 'hidden',
  };

  const modalOverlayStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  };

  const modalContentStyle = {
    backgroundColor: '#1e1e1e',
    borderRadius: '8px',
    width: '90%',
    maxWidth: '700px',
    maxHeight: '80vh',
    display: 'flex',
    flexDirection: 'column',
    border: '1px solid #3e3e42',
  };

  const modalHeaderStyle = {
    padding: '16px',
    borderBottom: '1px solid #3e3e42',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };

  const modalTitleStyle = {
    fontSize: '18px',
    fontWeight: 'bold',
    color: 'rgb(76, 175, 80)',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  };

  const modalBodyStyle = {
    padding: '16px',
    overflowY: 'auto',
    flex: 1,
  };

  const citationItemStyle = {
    padding: '12px',
    marginBottom: '12px',
    backgroundColor: '#2a2d2e',
    borderRadius: '6px',
    borderLeft: '3px solid rgb(76, 175, 80)',
    transition: 'background-color 0.2s ease',
  };

  const citationTitleStyle = {
    fontSize: '14px',
    fontWeight: 'bold',
    color: '#cccccc',
    marginBottom: '6px',
  };

  const citationDescriptionStyle = {
    fontSize: '12px',
    color: '#858585',
    marginBottom: '8px',
    lineHeight: '1.5',
  };

  const citationAuthorStyle = {
    fontSize: '12px',
    color: '#858585',
    marginBottom: '8px',
    lineHeight: '1.5',
  };

  const citationLinkStyle = {
    fontSize: '12px',
    color: 'rgb(76, 175, 80)',
    textDecoration: 'none',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    transition: 'color 0.2s ease',
  };

  const modalCloseButtonStyle = {
    backgroundColor: 'transparent',
    border: 'none',
    color: '#cccccc',
    cursor: 'pointer',
    padding: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '4px',
  };

  return (
    <div style={containerStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <div style={headerLeftStyle}>
          <ShieldCheck size={16} color="rgb(76, 175, 80)" />
          <span style={titleStyle}>Data Seance</span>
          <button
            onClick={() => setShowCitationsModal(true)}
            style={iconButtonStyle}
            title="View Citations & Resources"
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#2a2d2e';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
          >
            <Info size={14} />
          </button>
        </div>
        <button
          onClick={onClose}
          style={closeButtonStyle}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#2a2d2e';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
          }}
        >
          <X size={16} />
        </button>
      </div>

      {/* Content */}
      <div style={contentStyle}>
        <ProblemsPanel 
          selectedFile={selectedFile}
          fileContents={fileContents}
        />
      </div>

      {/* Citations Modal */}
      {showCitationsModal && (
        <div style={modalOverlayStyle} onClick={() => setShowCitationsModal(false)}>
          <div style={modalContentStyle} onClick={(e) => e.stopPropagation()}>
            <div style={modalHeaderStyle}>
              <div style={modalTitleStyle}>
                <Info size={20} />
                <span>Citations & Resources</span>
              </div>
              <button
                onClick={() => setShowCitationsModal(false)}
                style={modalCloseButtonStyle}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2a2d2e'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <X size={20} />
              </button>
            </div>
            <div style={modalBodyStyle}>
              <div style={{ marginBottom: '16px', color: '#cccccc', fontSize: '14px' }}>
                This tool is built upon ethical AI guidelines and regulations from leading organizations worldwide.
              </div>
              {citations.map((citation, index) => (
                <div
                  key={index}
                  style={citationItemStyle}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#323436';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#2a2d2e';
                  }}
                >
                  <div style={citationTitleStyle}>{citation.title}</div>
                  <div style={citationDescriptionStyle}>{citation.description}</div>
                  <p style={citationAuthorStyle}>{citation.author}</p>
                  <a
                    href={citation.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={citationLinkStyle}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.color = '#5cb85c';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.color = 'rgb(76, 175, 80)';
                    }}
                  >
                    🔗 {citation.url}
                  </a>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}